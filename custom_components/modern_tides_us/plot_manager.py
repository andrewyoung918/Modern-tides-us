"""Plot management for Modern Tides integration."""
import datetime
import logging
import math
import base64
import io
from typing import Any, Dict, List, Optional, Tuple

from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class TidePlotManager:
    """Class to manage SVG-based tide plots."""

    def __init__(
        self,
        name: str,
        filename: str,
        transparent_background: bool = False,
        dark_mode: bool = False,
        plot_days: int = 1,
    ):
        """Initialize the plot manager."""
        self._name = name
        self._filename = filename
        self._transparent_background = transparent_background
        self._dark_mode = dark_mode
        self._plot_days = plot_days

    def generate_tide_plot(
        self, 
        tide_data: Dict[str, Any], 
        current_time: Optional[datetime.datetime] = None
    ) -> bool:
        """Generate a tide plot SVG from the given data."""
        if not tide_data:
            _LOGGER.warning("Cannot generate plot: no tide data provided")
            return False

        if current_time is None:
            current_time = dt_util.now()

        try:
            # Extract tide predictions
            predictions = self._extract_predictions(tide_data)
            if not predictions:
                _LOGGER.warning("No valid predictions found in tide data")
                return False

            # Generate interpolated curve points for smooth visualization
            curve_points = self._generate_smooth_curve(predictions, current_time)
            
            # Find extremes (high/low tides)
            extremes = self._find_extremes(predictions)
            
            # Get current height
            current_height = self._interpolate_current_height(predictions, current_time)
            
            # Generate SVG
            svg_content = self._generate_svg_plot(
                curve_points, 
                extremes, 
                current_time, 
                current_height,
                predictions
            )
            
            # Convert SVG to PNG and save
            return self._save_svg_as_png(svg_content)

        except Exception as e:
            _LOGGER.error(f"Error generating tide plot: {e}")
            return False

    def _extract_predictions(self, tide_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract prediction data from the processed tide data."""
        predictions = []
        
        # Check if we have multi-day data
        if "all_daily_data" in tide_data and tide_data["all_daily_data"] and self._plot_days > 1:
            _LOGGER.debug("Processing multi-day data for %d days", self._plot_days)
            
            # Process each day's data
            for day_data_info in tide_data["all_daily_data"]:
                day_data = day_data_info["data"]
                date_str = day_data_info["date"]
                
                # Parse date to get the day offset
                day_date = datetime.datetime.strptime(date_str, "%Y%m%d")
                # Convert to timezone-aware UTC first, then to local
                day_date = dt_util.utc_from_timestamp(day_date.timestamp())
                day_date = dt_util.as_local(day_date)
                
                # Extract predictions from this day
                if day_data and "mareas" in day_data and "datos" in day_data["mareas"]:
                    if "marea" in day_data["mareas"]["datos"]:
                        marea_data = day_data["mareas"]["datos"]["marea"]
                        
                        for point in marea_data:
                            if "hora" in point and "altura" in point:
                                try:
                                    time_str = point["hora"]  # Format is "HH:MM"
                                    height = float(point["altura"])
                                    
                                    # Parse time and combine with the correct date
                                    time_parts = time_str.split(":")
                                    hours = int(time_parts[0])
                                    minutes = int(time_parts[1])
                                    
                                    # Create datetime for this specific day
                                    # API returns local times (lst_ldt), so combine with the day date
                                    dt = day_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                                    # Make timezone-aware using Home Assistant's timezone
                                    dt = dt_util.as_local(dt)
                                    
                                    predictions.append({
                                        'time': dt,
                                        'height': height
                                    })
                                except (ValueError, TypeError) as e:
                                    _LOGGER.debug(f"Skipping invalid prediction entry: {e}")
                                    continue
            
            # Sort by time to ensure chronological order
            predictions.sort(key=lambda x: x['time'])
            _LOGGER.debug("Extracted %d multi-day predictions", len(predictions))
            
        # Check if we have processed tide_points in the data (single day or fallback)
        elif "tide_points" in tide_data and tide_data["tide_points"]:
            predictions = tide_data["tide_points"]
            _LOGGER.debug("Using %d processed tide points", len(predictions))
        else:
            # Fallback to original API structure parsing
            _LOGGER.debug("Tide data structure: %s", tide_data.keys() if tide_data else "No data")
            if "daily" in tide_data:
                _LOGGER.debug("Daily data keys: %s", tide_data["daily"].keys())
                if "mareas" in tide_data["daily"]:
                    _LOGGER.debug("Mareas data keys: %s", tide_data["daily"]["mareas"].keys())
            
            # Navigate through the API response structure
            if "daily" in tide_data and "mareas" in tide_data["daily"]:
                mareas_data = tide_data["daily"]["mareas"]
                
                # Get prediction data
                if "prediccion" in mareas_data:
                    prediccion = mareas_data["prediccion"]
                    _LOGGER.debug("Found %d prediction entries", len(prediccion))
                    
                    for entry in prediccion:
                        try:
                            # Parse datetime
                            fecha_str = entry.get("fecha")
                            hora_str = entry.get("hora")
                            if fecha_str and hora_str:
                                # Combine date and time
                                datetime_str = f"{fecha_str} {hora_str}"
                                dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                                # API returns local times (lst_ldt), make timezone-aware
                                dt = dt_util.as_local(dt)
                                
                                # Get height
                                height = float(entry.get("altura", 0))
                                
                                predictions.append({
                                    'time': dt,
                                    'height': height
                                })
                        except (ValueError, TypeError) as e:
                            _LOGGER.debug(f"Skipping invalid prediction entry: {e}")
                            continue
                else:
                    _LOGGER.debug("No 'prediccion' key found in mareas data")
            else:
                _LOGGER.debug("Missing required keys in tide data structure")
        
        _LOGGER.debug("Extracted %d valid predictions", len(predictions))
        return predictions

    def _generate_smooth_curve(
        self,
        predictions: List[Dict[str, Any]],
        current_time: datetime.datetime
    ) -> List[Dict[str, Any]]:
        """Generate smooth curve points (NOAA data is already at 6-min intervals, so just sort)."""
        if len(predictions) < 2:
            return predictions

        # Sort predictions by time - NOAA provides 6-minute interval data
        # which is already dense enough for smooth visualization
        return sorted(predictions, key=lambda x: x['time'])

    def _interpolate_current_height(
        self, 
        predictions: List[Dict[str, Any]], 
        current_time: datetime.datetime
    ) -> Optional[float]:
        """Interpolate the current tide height."""
        if len(predictions) < 2:
            return None

        # Find the two predictions that bracket the current time
        for i in range(len(predictions) - 1):
            if predictions[i]['time'] <= current_time <= predictions[i + 1]['time']:
                # Linear interpolation
                t1, h1 = predictions[i]['time'], predictions[i]['height']
                t2, h2 = predictions[i + 1]['time'], predictions[i + 1]['height']
                
                # Calculate time ratios
                total_seconds = (t2 - t1).total_seconds()
                elapsed_seconds = (current_time - t1).total_seconds()
                
                if total_seconds == 0:
                    return h1
                
                ratio = elapsed_seconds / total_seconds
                interpolated_height = h1 + (h2 - h1) * ratio
                
                return interpolated_height

        return None

    def _find_extremes(self, predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find high and low tide extremes in the predictions."""
        if len(predictions) < 3:
            return []

        extremes = []

        for i in range(0, len(predictions)):
            if i == 0:
                prev_height = predictions[i]['height']
                curr_height = predictions[i]['height']
                next_height = predictions[i + 1]['height']
            elif i == (len(predictions) - 1):
                prev_height = predictions[i - 1]['height']
                curr_height = predictions[i]['height']
                next_height = predictions[i]['height']
            else:
                prev_height = predictions[i - 1]['height']
                curr_height = predictions[i]['height']
                next_height = predictions[i + 1]['height']

            # High tide: peak
            if curr_height >= prev_height and curr_height >= next_height:
                extremes.append({
                    'time': predictions[i]['time'],
                    'height': curr_height,
                    'type': 'high'
                })

            # Low tide: trough
            elif curr_height <= prev_height and curr_height <= next_height:
                extremes.append({
                    'time': predictions[i]['time'],
                    'height': curr_height,
                    'type': 'low'
                })

        return extremes

    def _generate_svg_plot(
        self,
        curve_points: List[Dict[str, Any]],
        extremes: List[Dict[str, Any]],
        current_time: datetime.datetime,
        current_height: Optional[float],
        original_predictions: List[Dict[str, Any]]
    ) -> str:
        """Generate SVG content for the tide plot."""
        
        # SVG dimensions
        width, height = 800, 400
        margin = 60
        plot_width = width - 2 * margin
        plot_height = height - 2 * margin
        
        # Get time and height ranges
        if not curve_points:
            return self._generate_error_svg()
            
        times = [p['time'] for p in curve_points]
        heights = [p['height'] for p in curve_points]
        
        min_time, max_time = min(times), max(times)
        min_height, max_height = min(heights), max(heights)
        
        # Add some padding to height range
        height_range = max_height - min_height
        min_height -= height_range * 0.1
        max_height += height_range * 0.1
        
        # Define color scheme based on mode - High-contrast sci-fi aesthetic
        if self._dark_mode:
            colors = {
                'background': '#0a0e14' if not self._transparent_background else 'none',  # Deep space blue-black
                'grid': '#1a2332',  # Subtle grid for depth
                'tide_line': '#00f6ff',  # Bright cyan (neon blue)
                'tide_fill': '#00f6ff',  # Cyan fill with opacity
                'tide_fill_opacity': '0.15',
                'current_marker': '#ff00ff',  # Magenta marker
                'current_text': '#00f6ff',   # Cyan text
                'high_tide': '#ff0080',   # Hot pink/magenta for high tide
                'low_tide': '#00ff9f',    # Neon green for low tide
                'text': '#e0e0e0',        # Near-white text
                'title': '#00f6ff',       # Cyan title
                'axis_text': '#8899aa',   # Muted blue-gray for axis text
            }
        else:
            colors = {
                'background': '#f5f5f5' if not self._transparent_background else 'none',  # Light gray background
                'grid': '#d0d0d0',
                'tide_line': '#0099ff',  # Bright blue
                'tide_fill': '#0099ff',  # Blue fill
                'tide_fill_opacity': '0.2',
                'current_marker': '#ff0080',  # Hot pink marker
                'current_text': '#000000',
                'high_tide': '#ff0066',   # Vibrant pink for high tide
                'low_tide': '#00cc88',    # Teal for low tide
                'text': '#1a1a1a',        # Near-black text
                'title': '#0066cc',       # Deep blue title
                'axis_text': '#4a4a4a',   # Dark gray for axis text
            }
        
        # Helper functions for coordinate conversion
        def time_to_x(time_val):
            time_ratio = (time_val - min_time).total_seconds() / (max_time - min_time).total_seconds()
            return margin + time_ratio * plot_width
            
        def height_to_y(height_val):
            height_ratio = (height_val - min_height) / (max_height - min_height)
            return height - margin - height_ratio * plot_height
        
        # Start building SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="{colors["background"]}"/>',
        ]
        
        # Add grid
        svg_parts.extend(self._generate_grid(margin, plot_width, plot_height, width, height, colors['grid']))
        
        # Generate tide curve path
        path_points = []
        for point in curve_points:
            x = time_to_x(point['time'])
            y = height_to_y(point['height'])
            path_points.append(f"{x},{y}")
        
        if path_points:
            path_data = f"M {path_points[0]} L " + " L ".join(path_points[1:])

            # Add filled area under curve (like matplotlib's fill_between)
            area_points = path_points.copy()
            # Add bottom line
            bottom_y = height_to_y(min_height)
            area_points.append(f"{time_to_x(max_time)},{bottom_y}")
            area_points.append(f"{time_to_x(min_time)},{bottom_y}")
            area_path = f"M {area_points[0]} L " + " L ".join(area_points[1:]) + " Z"

            svg_parts.append(f'<path d="{area_path}" fill="{colors["tide_fill"]}" opacity="{colors["tide_fill_opacity"]}"/>')

            # Single clean tide line
            svg_parts.append(f'<path d="{path_data}" stroke="{colors["tide_line"]}" stroke-width="2" fill="none"/>')
        
        # Add current position marker
        if current_height is not None:
            curr_x = time_to_x(current_time)
            curr_y = height_to_y(current_height)

            svg_parts.append(f'<circle cx="{curr_x}" cy="{curr_y}" r="4" fill="{colors["current_marker"]}"/>')

            # Add current time annotation
            curr_label = f'{current_height:.2f}m @ {current_time.strftime("%H:%M")}'
            svg_parts.append(f'''
                <text x="{curr_x}" y="{curr_y - 15}" text-anchor="middle" font-family="'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif" font-size="11" font-weight="500" fill="{colors["current_text"]}">
                    {curr_label}
                </text>
            ''')
        
        # Add extreme markers and labels
        for extreme in extremes:
            ext_x = time_to_x(extreme['time'])
            ext_y = height_to_y(extreme['height'])
            color = colors["high_tide"] if extreme['type'] == 'high' else colors["low_tide"]

            svg_parts.append(f'<circle cx="{ext_x}" cy="{ext_y}" r="4" fill="{color}"/>')

            # Add label
            label_y = ext_y - 20 if extreme['type'] == 'high' else ext_y + 25
            ext_label = f"{extreme['height']:.2f}m @ {extreme['time'].strftime('%H:%M')}"

            svg_parts.append(f'''
                <text x="{ext_x}" y="{label_y}" text-anchor="middle" font-family="'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif" font-size="11" font-weight="500" fill="{colors["text"]}">
                    {ext_label}
                </text>
            ''')
        
        # Add axes labels
        svg_parts.extend(self._generate_axes_labels(
            margin, plot_width, plot_height, width, height,
            min_time, max_time, min_height, max_height, colors['axis_text']
        ))
        
        # Add title with dynamic text based on plot days - modern font
        if self._plot_days == 1:
            title_text = f"TIDE PREDICTION - {self._name.upper()}"
        else:
            title_text = f"TIDE PREDICTION ({self._plot_days}D) - {self._name.upper()}"

        svg_parts.append(f'''
            <text x="{width/2}" y="25" text-anchor="middle" font-family="'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif" font-size="16" font-weight="700" letter-spacing="1" fill="{colors["title"]}">
                {title_text}
            </text>
        ''')
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)

    def _generate_grid(self, margin, plot_width, plot_height, width, height, grid_color="lightgray"):
        """Generate grid lines for the plot."""
        grid_parts = []
        
        # Vertical grid lines (time)
        for i in range(5):
            x = margin + (i * plot_width / 4)
            grid_parts.append(f'<line x1="{x}" y1="{margin}" x2="{x}" y2="{height - margin}" stroke="{grid_color}" stroke-width="0.5"/>')
        
        # Horizontal grid lines (height)
        for i in range(5):
            y = margin + (i * plot_height / 4)
            grid_parts.append(f'<line x1="{margin}" y1="{y}" x2="{width - margin}" y2="{y}" stroke="{grid_color}" stroke-width="0.5"/>')
        
        return grid_parts

    def _generate_axes_labels(self, margin, plot_width, plot_height, width, height,
                            min_time, max_time, min_height, max_height, text_color="black"):
        """Generate axes labels and ticks with modern font."""
        labels = []

        # X-axis (time) labels
        for i in range(5):
            x = margin + (i * plot_width / 4)
            time_ratio = i / 4
            label_time = min_time + (max_time - min_time) * time_ratio
            time_label = label_time.strftime("%H:%M")

            labels.append(f'<text x="{x}" y="{height - margin + 15}" text-anchor="middle" font-family="\'Segoe UI\', \'Roboto\', \'Helvetica Neue\', sans-serif" font-size="10" font-weight="500" fill="{text_color}">{time_label}</text>')

        # Y-axis (height) labels
        for i in range(5):
            y = height - margin - (i * plot_height / 4)
            height_ratio = i / 4
            label_height = min_height + (max_height - min_height) * height_ratio
            height_label = f"{label_height:.1f}m"

            labels.append(f'<text x="{margin - 10}" y="{y + 3}" text-anchor="end" font-family="\'Segoe UI\', \'Roboto\', \'Helvetica Neue\', sans-serif" font-size="10" font-weight="500" fill="{text_color}">{height_label}</text>')

        # Axis labels - uppercase for sci-fi aesthetic
        labels.append(f'<text x="{width/2}" y="{height - 10}" text-anchor="middle" font-family="\'Segoe UI\', \'Roboto\', \'Helvetica Neue\', sans-serif" font-size="11" font-weight="600" letter-spacing="0.5" fill="{text_color}">TIME</text>')
        labels.append(f'''
            <text x="15" y="{height/2}" text-anchor="middle" font-family="'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif" font-size="11" font-weight="600" letter-spacing="0.5" fill="{text_color}"
                  transform="rotate(-90, 15, {height/2})">TIDE HEIGHT (M)</text>
        ''')

        return labels

    def _generate_error_svg(self) -> str:
        """Generate an error SVG when no data is available."""
        bg_color = '#1e1e1e' if self._dark_mode and not self._transparent_background else ('none' if self._transparent_background else 'white')
        text_color = '#FF5722' if self._dark_mode else 'red'  # Orange for dark mode, red for light
        
        return f'''
        <svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="800" height="400" fill="{bg_color}"/>
            <text x="400" y="200" text-anchor="middle" font-family="Arial" font-size="18" fill="{text_color}">
                Could not load tide data
            </text>
        </svg>
        '''

    def _save_svg_as_png(self, svg_content: str) -> bool:
        """Save SVG content as PNG file."""
        try:
            # For now, save as SVG and let browsers handle it
            # This is compatible with Home Assistant camera entities
            with open(self._filename.replace('.png', '.svg'), 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            # Also create a simple PNG placeholder that references the SVG
            # We'll create a basic PNG with the SVG embedded as base64
            svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('ascii')
            
            # Create a simple HTML that can be served as image
            html_content = f'''
            <html>
            <body style="margin:0;padding:0;">
                <img src="data:image/svg+xml;base64,{svg_base64}" style="width:800px;height:400px;"/>
            </body>
            </html>
            '''
            
            # Save as both SVG and a data URI for flexibility
            with open(self._filename, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            _LOGGER.info(f"Tide plot saved successfully: {self._filename}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error saving tide plot: {e}")
            return False
