# MoveCRM Embeddable Widget

A lightweight, customizable JavaScript widget that allows customers to submit moving quote requests directly from any website.

## Features

- 🎨 **Fully Customizable** - Match your brand colors and styling
- 📱 **Mobile Responsive** - Works perfectly on all devices
- 🖼️ **Image Upload** - Customers can upload photos of items to move
- 🔒 **Secure** - All data is transmitted securely to your MoveCRM backend
- ⚡ **Lightweight** - Minimal impact on page load times
- 🌐 **Multi-tenant** - Supports multiple moving companies

## Quick Start

### 1. Include the Widget Script

Add the widget script to your website:

```html
<script src="https://cdn.movecrm.com/widget/movecrm-widget.js"></script>
```

### 2. Initialize the Widget

Add the initialization script with your configuration:

```html
<script>
  MoveCRMWidget.init({
    tenantSlug: 'your-company-slug',
    apiUrl: 'https://api.movecrm.com',
    primaryColor: '#2563eb'
  });
</script>
```

### 3. That's It!

The widget will automatically add a floating button to your page. Customers can click it to open the quote request form.

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `tenantSlug` | string | **required** | Your company's unique identifier |
| `apiUrl` | string | `'https://api.movecrm.com'` | MoveCRM API endpoint |
| `containerId` | string | `'movecrm-widget'` | Container element ID |
| `theme` | string | `'light'` | Widget theme (`'light'` or `'dark'`) |
| `primaryColor` | string | `'#2563eb'` | Primary brand color |
| `borderRadius` | string | `'8px'` | Border radius for rounded corners |
| `maxFileSize` | number | `52428800` | Maximum file size in bytes (50MB) |
| `allowedFileTypes` | array | `['image/jpeg', 'image/png', 'image/gif', 'image/webp']` | Allowed file types |
| `maxFiles` | number | `5` | Maximum number of files |

## Advanced Usage

### Custom Trigger Button

If you want to use your own button instead of the floating widget:

```html
<button onclick="MoveCRMWidget.open()">Get Moving Quote</button>

<script>
  MoveCRMWidget.init({
    tenantSlug: 'your-company-slug',
    // ... other options
  });
</script>
```

### Programmatic Control

```javascript
// Open the widget
MoveCRMWidget.open();

// Close the widget
MoveCRMWidget.close();

// Access configuration
console.log(MoveCRMWidget.config);

// Access current state
console.log(MoveCRMWidget.state);
```

### Custom Styling

You can override the default styles by adding CSS after the widget initialization:

```css
.movecrm-widget-trigger {
  background: #your-color !important;
  border-radius: 4px !important;
}

.movecrm-widget-modal {
  max-width: 800px !important;
}
```

## Form Fields

The widget collects the following information:

- **Full Name** (required)
- **Email Address** (required)
- **Phone Number** (optional)
- **Pickup Address** (required)
- **Delivery Address** (required)
- **Preferred Move Date** (optional)
- **Additional Notes** (optional)
- **Photos** (optional, up to 5 files)

## API Integration

The widget submits data to the `/public/quote` endpoint with the following structure:

```javascript
{
  name: "John Smith",
  email: "john@example.com",
  phone: "(555) 123-4567",
  pickup_address: "123 Main St, City, State",
  delivery_address: "456 Oak Ave, City, State",
  move_date: "2024-12-15",
  notes: "Need help with packing fragile items",
  files: [File, File, ...] // Uploaded images
}
```

## Browser Support

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Security

- All data is transmitted over HTTPS
- File uploads are validated on both client and server
- Rate limiting prevents abuse
- Multi-tenant isolation ensures data security

## Customization Examples

### Matching Your Brand

```javascript
MoveCRMWidget.init({
  tenantSlug: 'acme-moving',
  primaryColor: '#ff6b35',
  borderRadius: '12px',
  theme: 'light'
});
```

### Different File Limits

```javascript
MoveCRMWidget.init({
  tenantSlug: 'premium-movers',
  maxFiles: 10,
  maxFileSize: 100 * 1024 * 1024, // 100MB
  allowedFileTypes: ['image/jpeg', 'image/png', 'application/pdf']
});
```

## Development

### Local Development

1. Clone the repository
2. Open `examples/demo.html` in your browser
3. Modify `src/movecrm-widget.js` as needed

### Building for Production

```bash
# Minify the widget
npm run build

# The minified file will be in dist/movecrm-widget.min.js
```

## Support

For technical support or questions:

- 📧 Email: support@movecrm.com
- 📖 Documentation: https://docs.movecrm.com
- 🐛 Issues: https://github.com/movecrm/widget/issues

## License

MIT License - see LICENSE file for details.

