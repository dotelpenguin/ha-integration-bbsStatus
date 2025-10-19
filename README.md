# BBS Status Home Assistant Integration

A Home Assistant custom integration to monitor WWIV BBS (Bulletin Board System) status with health status endpoint monitoring.

## Features

- Monitor BBS status endpoint
- Track number of instances and usage
- Real-time status updates
- Configurable scan interval
- Support for custom host/port configuration

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Install "BBS Status" from the HACS store
3. Restart Home Assistant
4. Add the integration via the UI

### Manual Installation

1. Copy the `custom_components/bbs_status` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "BBS Status"
3. Enter your BBS server details:
   - **Host/IP Address**: The IP address or hostname of your BBS server
   - **Port**: The port number (default: 8080)
   - **Scan Interval**: How often to check the status in seconds (default: 60)

## Expected API Format

The integration expects your BBS to provide a JSON endpoint at `http://{host}:{port}/status` with the following format:

```json
{
    "status": {
        "num_instances": 11,
        "used_instances": 0,
        "lines": [
            "BINKP Waiting for Call",
            "StarDoc 134 Node #2 Waiting For Call",
            "StarDoc 134 Node #3 Waiting for Call",
            "StarDoc 134 Node #4 Waiting for Call",
            "StarDoc 134 Node #5 Waiting for Call",
            "StarDoc 134 Node #6 Waiting for Call",
            "StarDoc 134 Node #7 Waiting for Call",
            "StarDoc 134 Node #8 Waiting for Call",
            "StarDoc 134 Node #9 Waiting for Call",
            "StarDoc 134 Node #10 Waiting for Call",
            "StarDoc 134 Node #11 Waiting for Call"
        ]
    }
}
```

## Entities

The integration creates a sensor entity with the following attributes:

- **State**: Overall status (All Available, X/Y Used, All Busy)
- **num_instances**: Total number of instances
- **used_instances**: Number of currently used instances
- **available_instances**: Number of available instances
- **lines**: Array of status lines from the BBS

## Icons

- 🟢 Green circle: All instances available
- 🟡 Yellow circle: Some instances in use
- 🔴 Red circle: All instances busy

## Troubleshooting

### Connection Issues

- Verify the BBS server is running and accessible
- Check that the port is correct and not blocked by firewall
- Ensure the `/status` endpoint returns valid JSON

### Integration Not Found

- Make sure the integration files are in the correct location
- Restart Home Assistant after installation
- Check the Home Assistant logs for any errors

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/dotelpenguin/ha-integration-bbsStatus).

## License

This project is licensed under the MIT License.
