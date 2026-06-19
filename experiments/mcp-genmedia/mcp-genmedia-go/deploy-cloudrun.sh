#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This script provides an automated workflow to deploy Go MCP servers
# to Google Cloud Run as private Streamable HTTP endpoints.

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

find_mcp_servers() {
  # Excluding mcp-imagen-go if deprecated, keeping others
  find . -mindepth 1 -maxdepth 1 -type d -name 'mcp-*-go' ! -name 'mcp-imagen-go' | sed 's|./||'
}

check_gcloud() {
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}gcloud CLI is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
  fi
}

main() {
  check_gcloud

  # Resolve Project ID
  if [[ -z "${GOOGLE_CLOUD_PROJECT}" ]] && [[ -n "${PROJECT_ID}" ]]; then
    export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
  fi

  if [[ -z "${GOOGLE_CLOUD_PROJECT}" ]]; then
    echo -e "${YELLOW}GOOGLE_CLOUD_PROJECT not set, retrieving from gcloud config...${NC}"
    GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [[ -z "${GOOGLE_CLOUD_PROJECT}" ]]; then
      echo -e "${RED}ERROR: Could not retrieve GOOGLE_CLOUD_PROJECT. Please set it manually.${NC}"
      echo "Example: export GOOGLE_CLOUD_PROJECT=your-gcp-project-id"
      exit 1
    fi
  fi
  echo -e "${GREEN}Project ID: ${GOOGLE_CLOUD_PROJECT}${NC}"

  # Prompt/Select Region
  read -p "Select Deployment Region [us-central1]: " REGION
  REGION=${REGION:-us-central1}
  echo -e "${GREEN}Region: ${REGION}${NC}"

  # Select MCP Server to Deploy
  echo -e "\n${BLUE}Please choose an MCP server to deploy to Cloud Run:${NC}"
  select server in $(find_mcp_servers) "Exit"; do
    case $server in
      "Exit")
        echo "Exiting."
        exit 0
        ;;
      *)
        if [ -n "$server" ]; then
          SERVER_NAME=$server
          break
        else
          echo -e "${RED}Invalid selection.${NC}"
        fi
        ;;
    esac
  done

  echo -e "\n${BLUE}Starting deployment for ${SERVER_NAME}...${NC}"

  # 1. Verify/Create Artifact Registry Repository
  echo -e "${YELLOW}[1/4] Verifying Artifact Registry repository 'mcp-servers'...${NC}"
  if ! gcloud artifacts repositories describe mcp-servers --location=${REGION} &>/dev/null; then
    echo "Creating Docker repository 'mcp-servers' in ${REGION}..."
    gcloud artifacts repositories create mcp-servers \
      --repository-format=docker \
      --location=${REGION} \
      --description="Repository for hosted MCP servers" || {
        echo -e "${RED}ERROR: Failed to create Artifact Registry repository.${NC}"
        exit 1
      }
  else
    echo -e "${GREEN}Repository 'mcp-servers' already exists.${NC}"
  fi

  # 2. Build Container Image via Cloud Build
  echo -e "\n${YELLOW}[2/4] Building container image in the cloud via Cloud Build...${NC}"
  IMAGE_TAG="${REGION}-docker.pkg.dev/${GOOGLE_CLOUD_PROJECT}/mcp-servers/${SERVER_NAME}:latest"
  
  if ! gcloud builds submit . \
    --config=cloudbuild.yaml \
    --substitutions=_IMAGE=${IMAGE_TAG},_SERVER_NAME=${SERVER_NAME}; then
      echo -e "${RED}ERROR: Cloud Build failed.${NC}"
      exit 1
  fi
  echo -e "${GREEN}Container image built successfully: ${IMAGE_TAG}${NC}"

  # 3. Deploy to Cloud Run
  echo -e "\n${YELLOW}[3/4] Deploying service to Cloud Run (Private)...${NC}"
  if ! gcloud run deploy ${SERVER_NAME} \
    --image=${IMAGE_TAG} \
    --region=${REGION} \
    --port=8080 \
    --no-allow-unauthenticated \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},LOCATION=${REGION}; then
      echo -e "${RED}ERROR: Cloud Run deployment failed.${NC}"
      exit 1
  fi

  # Get Service URL
  SERVICE_URL=$(gcloud run services describe ${SERVER_NAME} --region=${REGION} --format="value(status.url)")
  echo -e "${GREEN}Cloud Run Service deployed successfully!${NC}"
  echo -e "URL: ${BLUE}${SERVICE_URL}${NC}"

  # 4. Bind IAM Roles (Optional)
  echo -e "\n${YELLOW}[4/4] Configuring IAM Roles...${NC}"
  SERVICE_ACCOUNT=$(gcloud run services describe ${SERVER_NAME} --region=${REGION} --format="value(spec.template.spec.serviceAccountName)")
  echo "Service account identified: $SERVICE_ACCOUNT"

  read -p "Would you like to grant Vertex AI User and GCS Object Admin roles to this service account? (y/N): " grant_iam
  case "$grant_iam" in
    [yY]|[yY][eE][sS])
      echo "Granting Vertex AI User..."
      gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/aiplatform.user" >/dev/null
      
      echo "Granting Storage Object Admin..."
      gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/storage.objectAdmin" >/dev/null
      
      echo -e "${GREEN}IAM configuration complete.${NC}"
      ;;
    *)
      echo "Skipping IAM bindings configuration."
      ;;
  esac

  echo -e "\n${GREEN}Deployment Complete!${NC}"
  echo -e "To configure this server in Gemini Enterprise, use the following endpoint URL:"
  echo -e "  ${BLUE}${SERVICE_URL}/mcp${NC}\n"
}

main
