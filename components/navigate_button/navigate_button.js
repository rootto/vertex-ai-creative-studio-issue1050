import { LitElement, html, css } from 'https://esm.sh/lit@3.1.2';

export class NavigateButton extends LitElement {
  static properties = {
    label: { type: String },
    url: { type: String },
  };

  static styles = css`
    button {
      background-color: #0a58ca;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
      font-family: inherit;
      font-size: 14px;
      font-weight: 500;
      text-transform: uppercase;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
      transition: background-color 0.3s, box-shadow 0.3s;
    }
    button:hover {
      background-color: #0b5ed7;
      box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    button:active {
      background-color: #0a58ca;
      box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
  `;

  render() {
    return html`
      <button @click="${this.handleClick}">${this.label}</button>
    `;
  }

  handleClick() {
    window.location.href = this.url;
  }
}

customElements.define('navigate-button', NavigateButton);
