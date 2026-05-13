import json
import c2pa
import os

def get_c2pa_manifest(video_path):
    """
    Extracts the C2PA manifest from a video file using the c2pa.Reader.
    """
    if not os.path.exists(video_path):
        return {"error": f"File not found: {video_path}"}
        
    try:
        reader = c2pa.Reader(str(video_path))
        manifest_json = reader.json()
        
        if not manifest_json:
            return {"error": "No C2PA manifest found in this file."}
        
        return json.loads(manifest_json)
    except Exception as e:
        return {"error": f"C2PA Read Error: {str(e)}"}

def summarize_c2pa(video_path):
    """
    Provides a high-level summary of the C2PA data for reporting.
    """
    manifest = get_c2pa_manifest(video_path)
    if "error" in manifest:
        return {
            "status": "Error", 
            "error_detail": manifest["error"], 
            "actions": [], 
            "generator": "Unknown"
        }
    
    validation_status = manifest.get("validation_status", [])
    status_label = "Valid"
    if validation_status:
        codes = [s.get("code") for s in validation_status]
        if all(c == "signingCredential.untrusted" for c in codes):
            status_label = "Untrusted (Sandbox)"
        else:
            status_label = f"Invalid ({codes[0]})"

    active_manifest_id = manifest.get("active_manifest")
    active_manifest = manifest.get("manifests", {}).get(active_manifest_id, {})
    
    # Extract generator
    generator = "Unknown"
    gen_info = active_manifest.get("claim_generator_info", [])
    if gen_info and isinstance(gen_info, list):
        generator = gen_info[0].get("name", "Unknown")
    elif active_manifest.get("claim_generator"):
        generator = active_manifest.get("claim_generator")

    summary = {
        "status": status_label,
        "generator": generator,
        "actions": []
    }
    
    # Gather detailed actions
    assertions = active_manifest.get("assertions", [])
    for assertion in assertions:
        label = assertion.get("label", "")
        if "c2pa.actions" in label:
            actions_list = assertion.get("data", {}).get("actions", [])
            for action in actions_list:
                action_name = action.get("action", "unknown action")
                description = action.get("description", "")
                ds_type = action.get("digitalSourceType", "")
                
                # Format: action_name: description (ds_type)
                detail = f"{action_name}: {description}"
                if ds_type:
                    # Clean up DS type URL if present
                    ds_name = ds_type.split("/")[-1] if "/" in ds_type else ds_type
                    detail += f" ({ds_name})"
                
                summary["actions"].append({
                    "label": action_name,
                    "detail": detail
                })
                
    return summary
