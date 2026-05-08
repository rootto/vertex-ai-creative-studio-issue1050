import { LitElement, html } from 'https://esm.sh/lit@3.1.2';

export class LoginComponent extends LitElement {
  static get properties() {
    return {
      login: { type: String },
    };
  }

  constructor() {
    super();
    this.clientId = "356909977560-rm29g6coq1jim1l9cehkplvheriog962.apps.googleusercontent.com";
    this.login = "";
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadGisScript();
  }

  loadGisScript() {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => this.initializeGis();
    document.body.appendChild(script);
  }

  initializeGis() {
    if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
      google.accounts.id.initialize({
        client_id: this.clientId,
        callback: (response) => this.handleCredentialResponse(response),
      });
      google.accounts.id.renderButton(
        this.renderRoot.getElementById("login-button"),
        { theme: "outline", size: "large" }
      );
    } else {
      console.error("Google Identity Services script not loaded properly.");
      setTimeout(() => this.initializeGis(), 1000);
    }
  }

  handleCredentialResponse(response) {
    console.log("DEBUG: handleCredentialResponse called in JS", response);
    console.log("DEBUG: this.login value is:", this.login);
    if (this.login) {
      this.dispatchEvent(new MesopEvent(this.login, { value: response.credential }));
    } else {
      console.error("Login event handler property not set.");
    }
  }

  render() {
    return html`
      <div id="login-button"></div>
    `;
  }
}

customElements.define('login-component', LoginComponent);
