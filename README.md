# Modern Tides

Un componente personalizado para Home Assistant que proporciona datos de mareas en tiempo real para puertos españoles utilizando la API oficial del Instituto Hidrográfico de la Marina (IHM).

## Características

- Consulta de mareas en tiempo real para puertos españoles
- Muestra la altura actual de la marea
- Información detallada sobre la próxima marea alta y baja
- Gráfico visual de la curva de mareas
- Configuración personalizable del intervalo de actualización
- Soporte para múltiples puertos/estaciones de mareas

## Instalación

### Método HACS (recomendado)

1. Asegúrate de tener [HACS](https://hacs.xyz/) instalado.
2. Añade este repositorio como una integración personalizada en HACS:
   - Ve a HACS > Integraciones
   - Haz clic en los tres puntos en la esquina superior derecha
   - Selecciona "Repositorios personalizados"
   - Añade la URL del repositorio: `https://github.com/ALArvi019/moderntides`
   - Selecciona "Integración" como categoría
3. Busca "Modern Tides" en la tienda de HACS e instálalo
4. Reinicia Home Assistant

### Instalación manual

1. Descarga el último release desde el [repositorio de GitHub](https://github.com/ALArvi019/moderntides)
2. Copia la carpeta `custom_components/moderntides` a tu carpeta `<config>/custom_components/` de Home Assistant
3. Reinicia Home Assistant

## Configuración

1. Ve a Configuración > Integraciones
2. Haz clic en "Añadir integración"
3. Busca "Modern Tides" y selecciónalo
4. Sigue las instrucciones para añadir estaciones de mareas:
   - Selecciona la estación/puerto deseado
   - Configura un nombre personalizado (opcional)
   - Establece el intervalo de actualización (por defecto: 1 hora)
5. Puedes añadir tantas estaciones como necesites

## Entidades creadas

Por cada estación de mareas configurada, se crearán las siguientes entidades:

- **Sensor de información de la estación**: Información general sobre la estación de mareas
- **Sensor de altura actual**: Altura actual de la marea en metros
- **Sensor de próxima marea alta**: Hora de la próxima marea alta
- **Sensor de próxima marea baja**: Hora de la próxima marea baja
- **Cámara de curva de mareas**: Visualización gráfica de la curva de mareas del día

## Tarjeta personalizada

Aquí hay un ejemplo de una tarjeta personalizada de tipo `picture-elements` que puedes usar para visualizar los datos de mareas:

```yaml
type: picture-elements
camera_image: camera.marea_NOMBRE_ESTACION_curve_picture
elements:
  - entity: sensor.marea_NOMBRE_ESTACION_tide_station_info
    style:
      background-color: rgba(24, 24, 28, 0.3)
      bottom: 0
      color: white
      font-size: 14px
      left: 0
      line-height: 34px
      padding: 0 15px
      pointer-events: none
      transform: initial
      font-weight: bold
      width: 100%
    type: state-label
  - entity: sensor.marea_NOMBRE_ESTACION_current_tide_height
    style:
      color: white
      font-size: 12px
      line-height: 32px
      margin: 150px 5px
      pointer-events: none
      font-weight: bold
      right: 0
      top: 0
      transform: initial
    prefix: "Altura actual de la marea : "
    type: state-label
  - entity: sensor.marea_NOMBRE_ESTACION_next_high_tide_time
    style:
      color: white
      font-size: 12px
      line-height: 32px
      margin: 1px 35px
      pointer-events: none
      font-weight: bold
      right: 0
      top: 0
      transform: initial
    prefix: "Próxima marea alta : "
    type: state-label
  - entity: sensor.marea_NOMBRE_ESTACION_next_high_tide_height
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
    prefix: "Altura de la marea alta: "
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
  - entity: sensor.marea_NOMBRE_ESTACION_next_low_tide_time
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
    prefix: "Próxima marea baja : "
    type: state-label
  - entity: sensor.marea_NOMBRE_ESTACION_next_low_tide_height
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
    prefix: "Altura de la marea baja : "
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

Reemplaza `NOMBRE_ESTACION` con el nombre de tu estación (en minúsculas y con guiones bajos en lugar de espacios).

## Fuente de datos

Este componente utiliza la API pública del Instituto Hidrográfico de la Marina (IHM):

- API de estaciones: `https://ideihm.covam.es/api-ihm/getmarea?request=getlist&format=json`
- API de mareas diarias: `https://ideihm.covam.es/api-ihm/getmarea?request=gettide&id=STATION_ID&format=json&date=YYYYMMDD`
- API de mareas mensuales: `https://ideihm.covam.es/api-ihm/getmarea?request=gettide&id=STATION_ID&format=json&month=YYYYMM`

## Dependencias

- `requests`: Para realizar solicitudes HTTP a la API
- `matplotlib`: Para generar gráficos de curvas de mareas
- `numpy`: Para procesamiento de datos
- `Pillow`: Para procesamiento de imágenes

## Solución de problemas

Si encuentras algún problema con la integración:

1. Verifica los logs de Home Assistant para mensajes de error específicos
2. Asegúrate de que tu instancia de Home Assistant tiene conexión a Internet
3. Verifica que las dependencias están correctamente instaladas
4. Si el problema persiste, abre un issue en el [repositorio de GitHub](https://github.com/ALArvi019/moderntides/issues)

## Contribuir

¡Las contribuciones son bienvenidas! Si quieres mejorar este componente:

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Envía los cambios a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

---

Desarrollado por [ALArvi019](https://github.com/ALArvi019) - 2025
