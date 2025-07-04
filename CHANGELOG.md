# Changelog

## 1.0.0 (2025-07-04)

### Major Release
- **NEW**: Beautiful SVG tide chart visualization with camera entity
- **NEW**: Modern tide plots with smooth curves and professional styling
- **NEW**: Complete English translation of all components
- **IMPROVED**: Enhanced error handling and timezone management
- **IMPROVED**: Optimized data processing and rendering
- **REMOVED**: Cleaned up unused files and dependencies
- **DOCS**: Comprehensive dashboard examples and usage guides

### Features
- Real-time tide data visualization through camera entity
- SVG-based charts with smooth interpolated curves
- Professional styling with grid lines and color coding
- Multiple dashboard examples for various use cases
- Support for multiple stations simultaneously
- Efficient data updates and caching

## 0.1.9 (2025-07-03)

### Bug Fixes
- Removed external cairosvg dependencies that caused installation issues
- Reverted to SVG format for image visualization for compatibility
- Improved component robustness for systems without graphics libraries

## 0.1.8 (2025-07-03)

### Improvements
- Added SVG to PNG conversion to improve image compatibility
- Added cairosvg dependency for image conversion
- Improved camera visualization with PNG format

## 0.1.7 (2025-07-03)

### Bug Fixes
- Fixed issue with Curve Picture image visualization
- Correctly set content type for SVG camera

## 0.1.6 (2025-07-03)

### Bug Fixes
- Fixed issue with timestamp sensors (high/low tide) using timezone-aware datetime objects
- Improved tide data processing for better accuracy

## 0.1.5 (2025-07-03)

### Improvements
- Added more debug logging to facilitate troubleshooting
- Improved error handling during coordinator initialization
- Better detection and notification when coordinators are not found for stations

## 0.1.4 (2025-07-03)

### Improvements
- Fixes in multiple station identification
- Improved error messages for configuration issues

## 0.1.3 (2025-07-03)

### Improvements
- Centralization of data coordinators: single coordinator per station for all related sensors
- Improved data update management for multiple stations
- Increased logging for better tracking and debugging
- Fixed issue where not all stations were updated correctly

## 0.1.2 (2023-07-06)

### Mejoras
- Eliminación de dependencias innecesarias (matplotlib, numpy, Pillow)
- Implementación de SVG para mostrar información de mareas en lugar de gráficos generados
- Adaptación para soportar cambios en el formato de respuesta de la API (mareas/estaciones)

## 0.1.1 (2023-07-05)

### Mejoras
- Soporte para múltiples estaciones
- Configuración de intervalo de actualización por estación
- Flujo de configuración mejorado para añadir/modificar/eliminar estaciones

## 0.1.0 (2023-07-04)

### Características iniciales
- Integración con la API del IHM para datos de mareas
- Sensores para altura actual, próxima marea alta y baja
- Configuración a través de la interfaz de usuario
