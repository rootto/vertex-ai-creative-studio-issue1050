import { LitElement, html, css } from 'https://cdn.jsdelivr.net/npm/lit/+esm';

export class BananaButton extends LitElement {
  static properties = {
    selected: { type: Boolean, reflect: true },
    badge: { type: String },
    label: { type: String },
    modelName: { type: String },
    modelSelected: { type: String }
  };

  constructor() {
    super();
    this.selected = false;
    this.badge = '';
    this.label = '';
    this.modelName = '';
  }

  static styles = css`
    :host {
      display: inline-flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      font-family: var(--md-sys-typescale-body-medium-font-family-name, sans-serif);
      cursor: pointer;
    }

    .button-container {
      position: relative;
      width: 64px;
      height: 64px;
      border-radius: 16px;
      background-color: var(--md-sys-color-surface-container-high);
      border: 2px solid transparent;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease-in-out;
    }

    .button-container:hover {
      background-color: var(--md-sys-color-surface-container-highest);
    }

    :host([selected]) .button-container {
      background-color: var(--md-sys-color-primary-container, #eaddff);
      border-color: var(--md-sys-color-primary, #6750a4);
    }

    .icon {
      width: 40px;
      height: 40px;
    }

    .badge {
      position: absolute;
      bottom: -6px;
      right: -6px;
      background-color: var(--md-sys-color-tertiary, #7d5260);
      color: var(--md-sys-color-on-tertiary, #ffffff);
      font-size: 11px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.2);
      border: 2px solid var(--md-sys-color-surface, #fff);
    }

    .label {
      font-size: 12px;
      color: var(--md-sys-color-on-surface);
      text-align: center;
      font-weight: 500;
      max-width: 80px;
      line-height: 1.2;
    }

    :host([selected]) .label {
      color: var(--md-sys-color-primary, #6750a4);
      font-weight: 700;
    }
  `;

  _handleClick() {
    console.log("Banana button clicked! Model:", this.modelName, "Event:", this.modelSelected);
    this.dispatchEvent(new MesopEvent(this.modelSelected, { value: this.modelName }));
  }

  render() {
    return html`
      <div class="button-container" @click=${this._handleClick}>
        <svg class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg">
          <path d="M746.666667 234.666667c21.333333 0 149.333333-21.333333 149.333333 170.666666S618.666667 938.666667 234.666667 938.666667c-42.666667 0-85.333333-21.333333-85.333334-21.333334l-21.333333-64s21.333333-85.333333 149.333333-149.333333 218.944-117.632 273.344-172.010667C593.344 489.344 661.333333 405.333333 661.333333 341.333333c0-41.770667 42.666667-85.333333 42.666667-85.333333" fill="#FFE082" />
          <path d="M170.666667 874.666667s149.333333-42.666667 277.333333-106.666667 405.333333-256 320-533.333333c0 0 128-21.333333 128 170.666666S618.666667 938.666667 234.666667 938.666667c-42.666667 0-85.333333-21.333333-85.333334-21.333334l21.333334-42.666666z" fill="#FFCA28" />
          <path d="M876.010667 297.344C836.010667 211.562667 746.666667 256 746.666667 85.333333c-64 0-106.666667 42.666667-106.666667 42.666667s64 64 64 128c42.666667 0 77.056-3.349333 80.874667 101.333333 28.842667-122.218667 91.136-59.989333 91.136-59.989333z" fill="#C0CA33" />
          <path d="M661.333333 341.333333s-1.344-38.677333 42.666667-85.333333 85.994667-8.661333 85.994667-8.661333l-5.12 109.994666s-18.666667-69.333333-48-71.104C675.008 282.496 661.333333 341.333333 661.333333 341.333333z" fill="#C0CA33" />
          <path d="M128 874.666667l21.333333 42.666666h21.333334v-42.666666l-42.666667-21.333334z" fill="#5D4037" />
          <path d="M746.666667 85.333333c-64 0-106.666667 42.666667-106.666667 42.666667h64l42.666667-42.666667z" fill="#827717" />
        </svg>
        ${this.badge ? html`<div class="badge">${this.badge}</div>` : ''}
      </div>
      ${this.label ? html`<div class="label">${this.label}</div>` : ''}
    `;
  }
}

customElements.define('banana-button', BananaButton);
