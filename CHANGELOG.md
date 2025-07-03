# Changelog

## 0.1.6 (2025-07-03)

### Correcciones
- Corregido el problema con los sensores de tipo timestamp (pleamar/bajamar) usando objetos datetime con zona horaria
- Mejorado el procesamiento de datos de mareas para mayor precisión

## 0.1.5 (2025-07-03)

### Mejoras
- Añadidos más registros de depuración para facilitar la resolución de problemas
- Mejorado el manejo de errores durante la inicialización de coordinadores
- Mejor detección y notificación cuando no se encuentran coordinadores para las estaciones

## 0.1.4 (2025-07-03)

### Mejoras
- Correcciones en la identificación de estaciones múltiples
- Mensajes de error mejorados para problemas de configuración

## 0.1.3 (2025-07-03)

### Mejoras
- Centralización de los coordinadores de datos: un único coordinador por estación para todos los sensores relacionados
- Mejora en la gestión de la actualización de datos para múltiples estaciones
- Incremento de los logs para mejor seguimiento y depuración
- Corrección del problema donde no se actualizaban todas las estaciones correctamente

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
