# Modern Tides

<img src="images/logo.png" alt="Modern Tides Logo" width="150" align="right" />

A custom component for Home Assistant that provides real-time tide data for Spanish ports using the official API of the Instituto Hidrográfico de la Marina (IHM).

## Features

- Real-time tide queries for Spanish ports
- Shows current tide height
- Detailed information about the next high and low tides
- Beautiful SVG tide charts with smooth curves
- Camera entity for displaying tide graphs in Lovelace
- Customizable update interval per station
- Support for multiple tide ports/stations simultaneously
- Efficient data updates for all stations

## Installation

### HACS Method (recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed.
2. Add this repository as a custom integration in HACS:
   - Go to HACS > Integrations
   - Click on the three dots in the upper right corner
   - Select "Custom repositories"
   - Add the repository URL: `https://github.com/ALArvi019/moderntides`
   - Select "Integration" as the category
3. Search for "Modern Tides" in the HACS store and install it
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [GitHub repository](https://github.com/ALArvi019/moderntides)
2. Copy the `custom_components/moderntides` folder to your Home Assistant `<config>/custom_components/` folder
3. Restart Home Assistant

## Configuration

1. Go to Configuration > Integrations
2. Click on "Add integration"
3. Search for "Modern Tides" and select it
4. Follow the instructions to add tide stations:
   - Select the desired station/port
   - Configure a custom name (optional)
   - Set the update interval (default: 1 hour)
5. You can add as many stations as you need

## Created Entities

For each configured tide station, the following entities will be created:

- **Station information sensor**: General information about the tide station
- **Current height sensor**: Current tide height in meters
- **Next high tide sensor**: Time and height of the next high tide
- **Next low tide sensor**: Time and height of the next low tide
- **Tide plot camera**: Beautiful graphical visualization of the day's tide curve

## Dashboard Examples

Here are various examples of how to display tide information in your Home Assistant dashboards. Replace `STATION_NAME` with your actual station name (in lowercase with underscores instead of spaces).

### 1. Simple Entities Card

```yaml
type: entities
title: Tide Information - STATION_NAME
entities:
  - entity: sensor.STATION_NAME_tide_station_info
    name: Station
    icon: mdi:anchor
  - entity: sensor.STATION_NAME_current_tide_height
    name: Current Height
    icon: mdi:waves
  - entity: sensor.STATION_NAME_next_high_tide_time
    name: Next High Tide
    icon: mdi:arrow-up-bold
  - entity: sensor.STATION_NAME_next_low_tide_time
    name: Next Low Tide
    icon: mdi:arrow-down-bold
```

### 2. Picture Elements Card with Tide Chart

```yaml
type: picture-elements
camera_image: camera.STATION_NAME_tide_plot
elements:
  - entity: sensor.STATION_NAME_tide_station_info
    style:
      background-color: rgba(0, 0, 0, 0.7)
      bottom: 0
      color: white
      font-size: 16px
      left: 0
      line-height: 40px
      padding: 0 20px
      pointer-events: none
      font-weight: bold
      width: 100%
    type: state-label
  - entity: sensor.STATION_NAME_current_tide_height
    style:
      background-color: rgba(0, 100, 200, 0.8)
      color: white
      font-size: 14px
      line-height: 30px
      padding: 5px 15px
      border-radius: 15px
      pointer-events: none
      font-weight: bold
      right: 10px
      top: 10px
    prefix: "Current: "
    suffix: " m"
    type: state-label
  - entity: sensor.STATION_NAME_next_high_tide_time
    style:
      background-color: rgba(0, 150, 0, 0.8)
      color: white
      font-size: 12px
      line-height: 25px
      padding: 3px 10px
      border-radius: 10px
      pointer-events: none
      font-weight: bold
      right: 10px
      top: 55px
    prefix: "↑ "
    type: state-label
  - entity: sensor.STATION_NAME_next_low_tide_time
    style:
      background-color: rgba(200, 0, 0, 0.8)
      color: white
      font-size: 12px
      line-height: 25px
      padding: 3px 10px
      border-radius: 10px
      pointer-events: none
      font-weight: bold
      right: 10px
      top: 90px
    prefix: "↓ "
    type: state-label
```

### 3. Glance Card

```yaml
type: glance
title: Tides Overview
entities:
  - entity: sensor.STATION_NAME_current_tide_height
    name: Current
    icon: mdi:waves
  - entity: sensor.STATION_NAME_next_high_tide_time
    name: Next High
    icon: mdi:arrow-up-bold
  - entity: sensor.STATION_NAME_next_low_tide_time
    name: Next Low
    icon: mdi:arrow-down-bold
```

### 4. Vertical Stack with Chart

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      # Tide Information - STATION_NAME
      Real-time tide data and predictions
  
  - type: picture-entity
    entity: camera.STATION_NAME_tide_plot
    camera_view: auto
    aspect_ratio: 2:1
  
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.STATION_NAME_current_tide_height
        min: 0
        max: 4
        name: Current Height
        unit: m
        severity:
          green: 1.5
          yellow: 0.5
          red: 0
      
      - type: entities
        entities:
          - entity: sensor.STATION_NAME_next_high_tide_time
            name: Next High Tide
            icon: mdi:arrow-up-bold
          - entity: sensor.STATION_NAME_next_low_tide_time
            name: Next Low Tide
            icon: mdi:arrow-down-bold
```

### 5. Multiple Stations Dashboard

```yaml
type: grid
title: Spanish Ports Tides
columns: 2
cards:
  - type: picture-elements
    camera_image: camera.cadiz_tide_plot
    elements:
      - entity: sensor.cadiz_tide_station_info
        style:
          bottom: 0
          left: 0
          background-color: rgba(0, 0, 0, 0.7)
          color: white
          font-size: 14px
          padding: 10px
          width: 100%
        type: state-label
  
  - type: picture-elements
    camera_image: camera.barcelona_tide_plot
    elements:
      - entity: sensor.barcelona_tide_station_info
        style:
          bottom: 0
          left: 0
          background-color: rgba(0, 0, 0, 0.7)
          color: white
          font-size: 14px
          padding: 10px
          width: 100%
        type: state-label
  
  - type: picture-elements
    camera_image: camera.valencia_tide_plot
    elements:
      - entity: sensor.valencia_tide_station_info
        style:
          bottom: 0
          left: 0
          background-color: rgba(0, 0, 0, 0.7)
          color: white
          font-size: 14px
          padding: 10px
          width: 100%
        type: state-label
  
  - type: picture-elements
    camera_image: camera.santander_tide_plot
    elements:
      - entity: sensor.santander_tide_station_info
        style:
          bottom: 0
          left: 0
          background-color: rgba(0, 0, 0, 0.7)
          color: white
          font-size: 14px
          padding: 10px
          width: 100%
        type: state-label
```

### 6. Compact Mobile-Friendly Card

```yaml
type: picture-elements
camera_image: camera.STATION_NAME_tide_plot
elements:
  - entity: sensor.STATION_NAME_current_tide_height
    style:
      top: 5px
      right: 5px
      background-color: rgba(0, 0, 0, 0.8)
      color: white
      padding: 5px 10px
      border-radius: 20px
      font-size: 12px
      font-weight: bold
    prefix: "Now: "
    suffix: "m"
    type: state-label
  
  - entity: sensor.STATION_NAME_next_high_tide_time
    style:
      top: 35px
      right: 5px
      background-color: rgba(0, 150, 0, 0.8)
      color: white
      padding: 3px 8px
      border-radius: 15px
      font-size: 10px
    prefix: "↑ "
    type: state-label
  
  - entity: sensor.STATION_NAME_next_low_tide_time
    style:
      top: 55px
      right: 5px
      background-color: rgba(200, 0, 0, 0.8)
      color: white
      padding: 3px 8px
      border-radius: 15px
      font-size: 10px
    prefix: "↓ "
    type: state-label
```

### 7. Card with Custom Styling

```yaml
type: picture-elements
camera_image: camera.STATION_NAME_tide_plot
elements:
  - type: custom:button-card
    entity: sensor.STATION_NAME_current_tide_height
    name: Current Tide
    show_state: true
    show_icon: false
    styles:
      card:
        - position: absolute
        - top: 10px
        - left: 10px
        - width: 120px
        - height: 60px
        - background-color: rgba(255, 255, 255, 0.9)
        - border-radius: 10px
        - font-size: 12px
      name:
        - font-weight: bold
        - color: "#333"
      state:
        - font-size: 18px
        - color: "#0066cc"
        - font-weight: bold
```

## Available Entities

After adding a station, you'll have access to these entities (replace `STATION_NAME` with your station's name):

- `sensor.STATION_NAME_tide_station_info` - Station information
- `sensor.STATION_NAME_current_tide_height` - Current tide height in meters
- `sensor.STATION_NAME_next_high_tide_time` - Next high tide time
- `sensor.STATION_NAME_next_low_tide_time` - Next low tide time
- `camera.STATION_NAME_tide_plot` - Tide chart visualization

## Data Source

This component uses the public API of the Instituto Hidrográfico de la Marina (IHM):

- Stations API: `https://ideihm.covam.es/api-ihm/getmarea?request=getlist&format=json`
- Daily tides API: `https://ideihm.covam.es/api-ihm/getmarea?request=gettide&id=STATION_ID&format=json&date=YYYYMMDD`
- Monthly tides API: `https://ideihm.covam.es/api-ihm/getmarea?request=gettide&id=STATION_ID&format=json&month=YYYYMM`

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
      font-size: 12px
      line-height: 32px
      margin: 1px 35px
      pointer-events: none
      font-weight: bold
      right: 0
      top: 0
      transform: initial
    prefix: "Next high tide: "
    type: state-label
  - entity: sensor.station_name_next_high_tide_height
    style:
      color: white
      font-size: 12px
      line-height: 32px
      margin: 30px 35px
      font-weight: bold
      pointer-events: none
      right: 0
      top: 0
      transform: initial
    prefix: "High tide height: "
    type: state-label
  - icon: mdi:arrow-up-bold
    style:
      color: white
      line-height: 32px
      margin: 39px 20px
      pointer-events: none
      right: 0
      top: 0
      transform: scale(0.8)
    type: icon
  - entity: sensor.station_name_next_low_tide_time
    style:
      color: white
      font-weight: bold
      font-size: 12px
      line-height: 32px
      margin: 59px 35px
      pointer-events: none
      right: 0
      top: 0
      transform: initial
    prefix: "Next low tide: "
    type: state-label
  - entity: sensor.station_name_next_low_tide_height
    style:
      color: white
      font-weight: bold
      font-size: 12px
      line-height: 32px
      margin: 84px 35px
      pointer-events: none
      right: 0
      top: 0
      transform: initial
    type: state-label
    prefix: "Low tide height: "
  - icon: mdi:arrow-down-bold
    style:
      color: white
      line-height: 40px
      margin: 88px 20px
      pointer-events: none
      right: 0
      top: 0
      transform: scale(0.8)
    type: icon
```

Replace `station_name` with your station's name (in lowercase and with underscores instead of spaces).

## Data Source

This component uses the public API of the Instituto Hidrográfico de la Marina (IHM):

- Stations API: `https://ideihm.covam.es/api-ihm/getmarea?request=getlist&format=json`
- Daily tides API: `https://ideihm.covam.es/api-ihm/getmarea?request=gettide&id=STATION_ID&format=json&date=YYYYMMDD`
- Monthly tides API: `https://ideihm.covam.es/api-ihm/getmarea?request=gettide&id=STATION_ID&format=json&month=YYYYMM`

## Dependencies

- `requests`: For making HTTP requests to the API

## Troubleshooting

If you encounter any issues with the integration:

1. Check Home Assistant logs for specific error messages
2. Make sure your Home Assistant instance has an Internet connection
3. Verify that dependencies are correctly installed
4. If the problem persists, open an issue in the [GitHub repository](https://github.com/ALArvi019/moderntides/issues)

## Contributing

Contributions are welcome! If you want to improve this component:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push the changes to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

Developed by [ALArvi019](https://github.com/ALArvi019) - 2025

## Custom Dashboards for Displaying Tide Data

Here are several examples of how to display tide information in custom Home Assistant dashboards, using different types of cards.

### Complete Tide Dashboard

Here's an example of a complete dashboard with multiple cards to display all data from a tide station (for example, "El Puerto de Santa María"):

```yaml
title: Tide Information
views:
  - title: Tides - El Puerto de Santa María
    cards:
      - type: vertical-stack
        cards:
          - type: markdown
            content: >
              # Tides - El Puerto de Santa María
              
              Updated information about port tides
          
          - type: entities
            title: General Data
            entities:
              - entity: sensor.el_puerto_tide_station_info
                name: Tide Station
              - entity: sensor.el_puerto_current_tide_height
                name: Current Height
                icon: mdi:waves
          
          - type: glance
            title: Upcoming Tides
            entities:
              - entity: sensor.el_puerto_next_high_tide_time
                name: Next High Tide
                icon: mdi:arrow-up-bold
              - entity: sensor.el_puerto_next_low_tide_time
                name: Next Low Tide
                icon: mdi:arrow-down-bold
          
          - type: picture-entity
            entity: camera.el_puerto_curve_picture
            camera_view: auto
            name: Tide Chart
```

### Entity Card

This card displays all tide data in a compact format:

```yaml
type: entities
title: Tides - El Puerto de Santa María
entities:
  - entity: sensor.el_puerto_tide_station_info
    name: Station
  - entity: sensor.el_puerto_current_tide_height
    name: Current Height
    icon: mdi:waves
  - type: divider
  - entity: sensor.el_puerto_next_high_tide_time
    name: Next High Tide
    icon: mdi:arrow-up-bold
  - entity: sensor.el_puerto_next_low_tide_time
    name: Next Low Tide
    icon: mdi:arrow-down-bold
  - type: divider
  - entity: camera.el_puerto_curve_picture
    name: Tide Chart
```

### Advanced Mushroom Card

If you have the custom Mushroom cards installed, you can create a more attractive visualization:

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: Tides - El Puerto de Santa María
    subtitle: Instituto Hidrográfico de la Marina
  
  - type: custom:mushroom-template-card
    primary: Current tide height
    secondary: "{{ states('sensor.el_puerto_current_tide_height') }} m"
    icon: mdi:waves
    icon_color: blue
  
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-template-card
        primary: Next high tide
        secondary: >-
          {{ states('sensor.el_puerto_next_high_tide_time') | as_timestamp | timestamp_custom('%H:%M') }}
        icon: mdi:arrow-up-bold
        icon_color: green
      
      - type: custom:mushroom-template-card
        primary: Next low tide
        secondary: >-
          {{ states('sensor.el_puerto_next_low_tide_time') | as_timestamp | timestamp_custom('%H:%M') }}
        icon: mdi:arrow-down-bold
        icon_color: red
  
  - type: picture-entity
    entity: camera.el_puerto_curve_picture
    camera_view: auto
```

### Multiple Stations in a Single Dashboard

If you have multiple stations configured, you can display them all in a single dashboard:

```yaml
type: grid
columns: 2
square: false
cards:
  # First station: El Puerto de Santa María
  - type: custom:mini-graph-card
    name: El Puerto de Santa María
    entities:
      - entity: sensor.el_puerto_current_tide_height
        name: Height
    hours_to_show: 24
    points_per_hour: 2
    icon: mdi:waves
    
  - type: entities
    title: El Puerto de Santa María
    entities:
      - entity: sensor.el_puerto_next_high_tide_time
        name: Next high tide
        icon: mdi:arrow-up-bold
      - entity: sensor.el_puerto_next_low_tide_time
        name: Next low tide
        icon: mdi:arrow-down-bold
        
  # Second station: Santander
  - type: custom:mini-graph-card
    name: Santander
    entities:
      - entity: sensor.santander_current_tide_height
        name: Height
    hours_to_show: 24
    points_per_hour: 2
    icon: mdi:waves
    
  - type: entities
    title: Santander
    entities:
      - entity: sensor.santander_next_high_tide_time
        name: Next high tide
        icon: mdi:arrow-up-bold
      - entity: sensor.santander_next_low_tide_time
        name: Next low tide
        icon: mdi:arrow-down-bold
```

### Custom Card with Weather Information

If you want to combine tide information with local weather:

```yaml
type: vertical-stack
cards:
  - type: weather-forecast
    entity: weather.openweathermap
    name: Weather in El Puerto de Santa María
    
  - type: custom:button-card
    entity: sensor.el_puerto_current_tide_height
    icon: mdi:waves
    name: Current Tide
    show_state: true
    styles:
      card:
        - background-color: var(--primary-color)
        - color: var(--text-primary-color)
      name:
        - font-size: 15px
      state:
        - font-size: 20px
    tap_action:
      action: more-info
      
  - type: custom:apexcharts-card
    header:
      title: Tide Forecast
      show: true
    series:
      - entity: sensor.el_puerto_current_tide_height
        type: line
        stroke_width: 3
        curve: smooth
        name: Tide Height
        color: blue
```

### Ejemplos de Paneles Personalizados

A continuación se muestran varios ejemplos de cómo mostrar la información de las mareas en los paneles de Home Assistant.

### Panel Básico

Para crear un panel básico con la información principal de tu estación (por ejemplo, "El Puerto de Santa María"):

```yaml
type: entities
title: Información de Mareas - El Puerto de Santa María
entities:
  - entity: sensor.el_puerto_tide_station_info
    name: Estación
    icon: mdi:information-outline
  - entity: sensor.el_puerto_current_tide_height
    name: Altura actual
    icon: mdi:waves
  - entity: sensor.el_puerto_next_high_tide_time
    name: Próxima pleamar
    icon: mdi:arrow-up-bold
  - entity: sensor.el_puerto_next_low_tide_time
    name: Próxima bajamar
    icon: mdi:arrow-down-bold
  - entity: camera.el_puerto_curve_picture
    name: Gráfico de marea
```

### Panel Completo con Imagen SVG

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Mareas El Puerto de Santa María
    entities:
      - entity: sensor.el_puerto_current_tide_height
        name: Altura actual de la marea
        icon: mdi:waves
      - entity: sensor.el_puerto_next_high_tide_time
        name: Próxima pleamar
        icon: mdi:arrow-up-bold
        secondary_info: attribute
        format: datetime
      - entity: sensor.el_puerto_next_low_tide_time
        name: Próxima bajamar
        icon: mdi:arrow-down-bold
        secondary_info: attribute
        format: datetime
  - type: picture-entity
    entity: camera.el_puerto_curve_picture
    camera_view: auto
    show_state: false
    show_name: false
```

### Panel con Información Adicional de Altura

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: >
      ## Mareas - El Puerto de Santa María
      
      **Altura actual:** {{ states('sensor.el_puerto_current_tide_height') }} m
      
      **Próxima pleamar:** {{ states('sensor.el_puerto_next_high_tide_time') | as_timestamp | timestamp_custom('%H:%M') }} ({{ state_attr('sensor.el_puerto_next_high_tide_time', 'height') }} m)
      
      **Próxima bajamar:** {{ states('sensor.el_puerto_next_low_tide_time') | as_timestamp | timestamp_custom('%H:%M') }} ({{ state_attr('sensor.el_puerto_next_low_tide_time', 'height') }} m)
  - type: picture-entity
    entity: camera.el_puerto_curve_picture
    camera_view: auto
```

## Automations with Tide Data

You can also create automations based on tide data. For example:

```yaml
# Automation that notifies you when it's one hour before the next high tide
automation:
  - alias: "High tide warning"
    trigger:
      - platform: template
        value_template: >
          {% set high_tide = states('sensor.el_puerto_next_high_tide_time') %}
          {% set time_diff = (as_timestamp(high_tide) - as_timestamp(now())) / 60 %}
          {{ time_diff > 59 and time_diff < 61 }}
    action:
      - service: notify.mobile_app
        data:
          title: "Tide Alert"
          message: "Approximately one hour until the next high tide"
```
