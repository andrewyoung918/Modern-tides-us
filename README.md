# Modern Tides - Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[hacs]: https://github.com/hacs/integration

A modern Home Assistant custom integration that provides real-time tide information and beautiful visualizations from US tide stations. This integration fetches data from the NOAA CO-OPS (Center for Operational Oceanographic Products and Services) API and provides sensors for current tide height, next high/low tide times, and a visual camera entity showing tide charts.

![Modern Tides Logo](images/logo.png)

## Credits

This US version is adapted from the original [Modern Tides](https://github.com/ALArvi019/moderntides) integration by [ALArvi019](https://github.com/ALArvi019), which provides tide data for Spanish coastal stations. We've modified it to work with NOAA CO-OPS tide stations for US coastal areas. Thank you to the original author for creating such a great foundation!

## Features

- **Real-time tide data** from official NOAA CO-OPS tide stations
- **Beautiful tide charts** as camera entities (SVG format)
- **Multi-day tide plots**: Automatically generates plots for 1-7 days
- **Dual visualization modes**: Light and dark theme support with automatic dual camera entities
- **Multiple sensors** for current height and next tide times
- **Easy configuration** through the UI
- **Automatic updates** every 30 minutes
- **Support for multiple stations** simultaneously
- **Modern UI integration** with optimized color palettes for both light and dark interfaces
- **Flexible plot selection**: Choose from 1-day to 7-day tide predictions in your dashboards

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS → Integrations
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/ALArvi019/moderntides`
5. Select "Integration" as the category
6. Click "Add"
7. Search for "Modern Tides" and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/ALArvi019/moderntides/releases)
2. Extract the contents to your `custom_components` directory:
   ```
   custom_components/
   └── moderntides/
       ├── __init__.py
       ├── manifest.json
       ├── config_flow.py
       ├── const.py
       ├── sensor.py
       ├── camera.py
       ├── tide_api.py
       ├── plot_manager.py
       └── strings.json
   ```
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Modern Tides"
4. Select your desired NOAA tide station from the dropdown list (defaults to Provincetown, MA)
5. Click **Submit**

The integration will automatically create all necessary entities for your selected station. If you're unsure which station to choose, the default Provincetown, MA station (8443970) provides excellent coverage for the Northeast US coast.

For each configured tide station, the following entities will be created:

- **Station information sensor**: General information about the tide station
- **Current height sensor**: Current tide height in meters
- **Next high tide sensor**: Time and height of the next high tide
- **Next low tide sensor**: Time and height of the next low tide
- **Tide plot cameras**: 14 camera entities for different time ranges and themes

## Available Entities

After adding a station, you'll have access to these entities (replace `STATION_NAME` with your station's name):

- `sensor.STATION_NAME_tide_station_info` - Station information
- `sensor.STATION_NAME_current_tide_height` - Current tide height in meters
- `sensor.STATION_NAME_next_high_tide_time` - Next high tide time
- `sensor.STATION_NAME_next_low_tide_time` - Next low tide time
- `camera.STATION_NAME_tide_plot` - Tide chart visualization (light mode)
- `camera.STATION_NAME_tide_plot_dark` - Tide chart visualization (dark mode)

### Camera Entities

The integration automatically creates **14 camera entities** for each station, giving you complete flexibility:

- **Light Mode Camera** (`camera.STATION_NAME_tide_plot`): Traditional white background with blue tide curves, perfect for light-themed dashboards
- `camera.STATION_NAME_tide_plot` - 1 day (default, backwards compatible)
- `camera.STATION_NAME_tide_plot_2d` - 2 days
- `camera.STATION_NAME_tide_plot_3d` - 3 days
- `camera.STATION_NAME_tide_plot_4d` - 4 days
- `camera.STATION_NAME_tide_plot_5d` - 5 days
- `camera.STATION_NAME_tide_plot_6d` - 6 days
- `camera.STATION_NAME_tide_plot_7d` - 7 days (1 week)

- **Dark Mode Camera** (`camera.STATION_NAME_tide_plot_dark`): Dark background (#1e1e1e) with green tide curves and enhanced contrast, optimized for dark-themed interfaces
- `camera.STATION_NAME_tide_plot_dark` - 1 day (default)
- `camera.STATION_NAME_tide_plot_2d_dark` - 2 days
- `camera.STATION_NAME_tide_plot_3d_dark` - 3 days
- `camera.STATION_NAME_tide_plot_4d_dark` - 4 days
- `camera.STATION_NAME_tide_plot_5d_dark` - 5 days
- `camera.STATION_NAME_tide_plot_6d_dark` - 6 days
- `camera.STATION_NAME_tide_plot_7d_dark` - 7 days (1 week)

### Visual Specifications

#### Light Mode (`camera.STATION_NAME_tide_plot`)
- **Background**: White (#FFFFFF)
- **Tide curve**: Cornflower blue (#6495ED)
- **Fill area**: Light blue with 30% opacity
- **Grid lines**: Light gray (#D3D3D3)
- **High tide markers**: Red (#FF0000)
- **Low tide markers**: Blue (#0000FF)
- **Text**: Black (#000000)

#### Dark Mode (`camera.STATION_NAME_tide_plot_dark`)
- **Background**: Dark gray (#1E1E1E)
- **Tide curve**: Green (#4CAF50)
- **Fill area**: Green with 20% opacity
- **Grid lines**: Dark gray (#404040)
- **High tide markers**: Orange (#FF5722)
- **Low tide markers**: Light blue (#2196F3)
- **Text**: White (#FFFFFF) and light gray (#CCCCCC)

Both visualizations are generated as scalable SVG files and update automatically with new tide data.

## Dashboard Examples

Explore our collection of dashboard examples to get the most out of your Modern Tides integration. Each example includes detailed instructions, YAML code, and visual previews.

| Example | Description | Features |
|---------|-------------|----------|
| [![Basic Entity Card](examples/01-basic-entity-card/preview.png)](examples/01-basic-entity-card/) | **[Basic Entity Card](examples/01-basic-entity-card/)** | Simple list format with all tide information |
| [![Picture Elements](examples/02-picture-elements-overlays/preview.png)](examples/02-picture-elements-overlays/) | **[Picture Elements with Overlays](examples/02-picture-elements-overlays/)** | Interactive overlays on tide chart |
| [![Glance Card](examples/03-glance-card/preview.png)](examples/03-glance-card/) | **[Glance Card](examples/03-glance-card/)** | Compact three-column view |
| [![Mushroom Cards](examples/04-mushroom-cards/preview.png)](examples/04-mushroom-cards/) | **[Mushroom Cards](examples/04-mushroom-cards/)** | Modern design with Mushroom components |
| [![Preferred Panel](examples/05-preferred-panel-configuration/preview.png)](examples/05-preferred-panel-configuration/) | **[Preferred Panel Configuration](examples/05-preferred-panel-configuration/)** | Most informative and visually appealing setup |
| [![Dark Mode](examples/06-dark-mode-visualization/preview.png)](examples/06-dark-mode-visualization/) | **[Dark Mode Visualization](examples/06-dark-mode-visualization/)** | Automatic theme switching and dual cameras |
| [![Comprehensive Weather](examples/07-comprehensive-weather-tides/preview.png)](examples/07-comprehensive-weather-tides/) | **[Comprehensive Weather & Tides](examples/07-comprehensive-weather-tides/)** | Complete weather and tide monitoring dashboard |
| [![Multiple Stations](examples/08-multiple-stations/preview.png)](examples/08-multiple-stations/) | **[Multiple Stations](examples/08-multiple-stations/)** | Side-by-side comparison dashboard |
| [![Multi-Day Plots](examples/09-multi-day-plots/preview.png)](examples/09-multi-day-plots/) | **[Multi-Day Plots](examples/09-multi-day-plots/)** | 1-7 day forecasts with automatic generation |

### Quick Start

1. Choose an example that fits your needs
2. Click on the example link to view detailed instructions
3. Replace `STATION_NAME` with your actual station name (e.g., `provincetown_ma`, `boston_ma`)
4. Copy the provided YAML code to your Home Assistant dashboard
5. Enjoy your beautiful tide visualizations!

### Requirements

- Modern Tides integration installed and configured
- For Mushroom card examples: [Mushroom cards](https://github.com/piitaya/lovelace-mushroom) custom component
- At least one tide station configured

## Example Automation

You can create automations based on tide data:

```yaml
automation:
  - alias: "High tide warning"
    trigger:
      - platform: template
        value_template: >
          {% set high_tide = states('sensor.STATION_NAME_next_high_tide_time') %}
          {% set time_diff = (as_timestamp(high_tide) - as_timestamp(now())) / 60 %}
          {{ time_diff > 59 and time_diff < 61 }}
    action:
      - service: notify.mobile_app
        data:
          title: "Tide Alert"
          message: "Approximately one hour until the next high tide at STATION_NAME"
```

## Data Source

This component uses the public NOAA CO-OPS (Center for Operational Oceanographic Products and Services) API:

- Base API: `https://tidesandcurrents.noaa.gov/api/datagetter`
- Stations API: `https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=tidepredictions`
- Predictions API: Uses `product=predictions` with station ID, date range, and format parameters
- Default station: **Provincetown, MA (ID: 8443970)**

The integration provides access to US coastal tide stations from NOAA's official tide and current prediction service.

### Finding NOAA Station IDs

You can find NOAA station IDs by:
- Using the integration's dropdown list of available stations
- Visiting [NOAA Tides & Currents](https://tidesandcurrents.noaa.gov/) and searching for your area
- Popular stations include:
  - 8443970: Provincetown, MA (default)
  - 8447930: Boston, MA  
  - 8518750: The Battery, NY
  - 8724580: Key West, FL

## Troubleshooting

If you encounter any issues with the integration:

1. Check Home Assistant logs for specific error messages
2. Make sure your Home Assistant instance has an Internet connection
3. Verify that the integration is properly installed
4. If the problem persists, open an issue in the [GitHub repository](https://github.com/ALArvi019/moderntides/issues)

## Contributing

Contributions are welcome! If you want to improve this component:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push the changes to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Developed by [ALArvi019](https://github.com/ALArvi019) - 2025

[commits-shield]: https://img.shields.io/github/commit-activity/y/ALArvi019/moderntides.svg?style=for-the-badge
[commits]: https://github.com/ALArvi019/moderntides/commits/main
[license-shield]: https://img.shields.io/github/license/ALArvi019/moderntides.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/ALArvi019/moderntides.svg?style=for-the-badge
[releases]: https://github.com/ALArvi019/moderntides/releases
