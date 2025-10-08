"""Plot management for Modern Tides integration."""
import datetime
import logging
import math
import base64
import io
from typing import Any, Dict, List, Optional, Tuple

from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class TideTableManager:
    """Class to manage SVG-based tide table schedules."""

    def __init__(
        self,
        name: str,
        filename: str,
        dark_mode: bool = False,
        table_days: int = 3,
    ):
        """Initialize the table manager."""
        self._name = name
        self._filename = filename
        self._dark_mode = dark_mode
        self._table_days = table_days

    def generate_tide_table(
        self,
        tide_data: Dict[str, Any],
        current_time: Optional[datetime.datetime] = None
    ) -> bool:
        """Generate a tide table SVG from the given data."""
        if not tide_data:
            _LOGGER.warning("Cannot generate table: no tide data provided")
            return False

        if current_time is None:
            current_time = dt_util.now()

        try:
            # Extract extremes (high/low tides) from the data
            extremes = self._extract_extremes(tide_data)

            if not extremes:
                _LOGGER.warning("No extremes found for tide table")
                return False

            # Generate SVG table
            svg_content = self._generate_svg_table(extremes, current_time)

            # Save SVG
            return self._save_svg(svg_content)

        except Exception as e:
            _LOGGER.error(f"Error generating tide table: {e}")
            return False

    def _extract_extremes(self, tide_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract high/low tide extremes from tide data."""
        extremes = []

        # Check if we have multi-day data
        if "all_daily_data" in tide_data and tide_data["all_daily_data"]:
            # Limit to the requested number of days
            days_to_process = min(self._table_days, len(tide_data["all_daily_data"]))

            for day_idx in range(days_to_process):
                day_data_info = tide_data["all_daily_data"][day_idx]
                day_data = day_data_info["data"]

                if day_data and "mareas" in day_data and "datos" in day_data["mareas"]:
                    if "marea" in day_data["mareas"]["datos"]:
                        marea_data = day_data["mareas"]["datos"]["marea"]

                        for point in marea_data:
                            if "tipo" in point and "hora" in point and "altura" in point:
                                # Parse time
                                time_str = point["hora"]
                                date_str = day_data_info["date"]

                                # Combine date and time
                                day_date = datetime.datetime.strptime(date_str, "%Y%m%d")
                                time_parts = time_str.split(":")
                                hours = int(time_parts[0])
                                minutes = int(time_parts[1])

                                dt = datetime.datetime(
                                    year=day_date.year,
                                    month=day_date.month,
                                    day=day_date.day,
                                    hour=hours,
                                    minute=minutes
                                )
                                dt = dt_util.as_local(dt)

                                extremes.append({
                                    'time': dt,
                                    'height': float(point["altura"]),
                                    'type': point["tipo"]
                                })

        return sorted(extremes, key=lambda x: x['time'])

    def _generate_svg_table(
        self,
        extremes: List[Dict[str, Any]],
        current_time: datetime.datetime
    ) -> str:
        """Generate SVG table content."""

        # SVG dimensions - make it wide enough for a readable table
        width, height = 600, 50 + (len(extremes) * 30) + 50  # Dynamic height based on rows

        # Color scheme
        if self._dark_mode:
            colors = {
                'background': '#000000',
                'text': '#FFFFFF',
                'title': '#FFFFFF',
                'high_tide': '#FF6B6B',
                'low_tide': '#4DABF7',
                'header': '#666666',
                'border': '#333333',
            }
        else:
            colors = {
                'background': '#FFFFFF',
                'text': '#000000',
                'title': '#000000',
                'high_tide': '#DC143C',
                'low_tide': '#1E90FF',
                'header': '#CCCCCC',
                'border': '#DDDDDD',
            }

        # Start SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<rect width="{width}" height="{height}" fill="{colors["background"]}"/>',
        ]

        # Title
        title_text = f"TIDE SCHEDULE ({self._table_days}D) - {self._name.upper()}"
        svg_parts.append(f'''
            <text x="{width/2}" y="25" text-anchor="middle" font-family="'Courier New', 'Courier', monospace" font-size="14" font-weight="bold" fill="{colors["title"]}">
                {title_text}
            </text>
        ''')

        # Table headers
        y_offset = 60
        col_widths = [120, 80, 100, 100]  # Day, Type, Time, Height
        col_x = [50, 170, 250, 350]

        headers = ["DATE", "TIDE", "TIME", "HEIGHT"]
        for i, header in enumerate(headers):
            svg_parts.append(f'''
                <text x="{col_x[i]}" y="{y_offset}" text-anchor="start" font-family="'Courier New', 'Courier', monospace" font-size="11" font-weight="bold" fill="{colors["header"]}">
                    {header}
                </text>
            ''')

        # Header separator line
        svg_parts.append(f'<line x1="40" y1="{y_offset + 5}" x2="{width - 40}" y2="{y_offset + 5}" stroke="{colors["border"]}" stroke-width="1"/>')

        # Table rows
        y_offset += 25
        current_date = None

        for extreme in extremes:
            # Only show future tides
            if extreme['time'] < current_time:
                continue

            is_high = extreme['type'] == 'pleamar'
            tide_color = colors['high_tide'] if is_high else colors['low_tide']

            # Date (only show if different from previous)
            date_str = extreme['time'].strftime("%a %m/%d")
            if date_str != current_date:
                current_date = date_str
                svg_parts.append(f'''
                    <text x="{col_x[0]}" y="{y_offset}" text-anchor="start" font-family="'Courier New', 'Courier', monospace" font-size="10" fill="{colors["text"]}">
                        {date_str}
                    </text>
                ''')

            # Tide type
            tide_type = "HIGH" if is_high else "LOW"
            svg_parts.append(f'''
                <text x="{col_x[1]}" y="{y_offset}" text-anchor="start" font-family="'Courier New', 'Courier', monospace" font-size="10" font-weight="bold" fill="{tide_color}">
                    {tide_type}
                </text>
            ''')

            # Time
            time_str = extreme['time'].strftime("%I:%M%p").lstrip('0')
            svg_parts.append(f'''
                <text x="{col_x[2]}" y="{y_offset}" text-anchor="start" font-family="'Courier New', 'Courier', monospace" font-size="10" fill="{colors["text"]}">
                    {time_str}
                </text>
            ''')

            # Height
            height_str = f"{extreme['height']:.1f}m"
            svg_parts.append(f'''
                <text x="{col_x[3]}" y="{y_offset}" text-anchor="start" font-family="'Courier New', 'Courier', monospace" font-size="10" fill="{colors["text"]}">
                    {height_str}
                </text>
            ''')

            y_offset += 30

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def _save_svg(self, svg_content: str) -> bool:
        """Save SVG content to file."""
        try:
            with open(self._filename, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            _LOGGER.debug("Saved tide table to %s", self._filename)
            return True
        except Exception as e:
            _LOGGER.error("Error saving tide table: %s", e)
            return False


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
        """Find high and low tide extremes from predictions with tipo field."""
        extremes = []

        for pred in predictions:
            # Check if this point has a tipo field indicating high or low tide
            if 'tipo' in pred:
                extremes.append({
                    'time': pred['time'],
                    'height': pred['height'],
                    'type': pred['tipo']  # 'pleamar' or 'bajamar'
                })

        _LOGGER.debug("Found %d tide extremes", len(extremes))
        return extremes

    def _generate_daylight_backgrounds(
        self,
        min_time: datetime.datetime,
        max_time: datetime.datetime,
        margin: int,
        height: int,
        plot_width: int,
        plot_height: int,
        time_to_x,
        colors: Dict[str, str]
    ) -> List[str]:
        """Generate daylight gradient backgrounds and sunrise/sunset markers."""
        elements = []

        # Approximate sunrise and sunset times (6 AM to 6 PM for simplicity)
        # In a production version, you'd use a library like astral for accurate times
        current_day = min_time.date()
        days_in_range = (max_time.date() - min_time.date()).days + 1

        for day_offset in range(days_in_range):
            day = current_day + datetime.timedelta(days=day_offset)

            # Approximate sunrise at 6 AM and sunset at 6 PM local time
            sunrise = dt_util.as_local(datetime.datetime.combine(day, datetime.time(6, 0)))
            sunset = dt_util.as_local(datetime.datetime.combine(day, datetime.time(18, 0)))

            # Only draw if sunrise/sunset fall within plot range
            if sunrise >= min_time and sunrise <= max_time:
                sunrise_x = time_to_x(sunrise)

                # Draw subtle daylight gradient from sunrise to sunset if sunset is also in range
                if sunset <= max_time:
                    sunset_x = time_to_x(sunset)
                    gradient_width = sunset_x - sunrise_x

                    # Subtle gradient background for daylight hours
                    opacity = 0.1 if not self._dark_mode else 0.05
                    elements.append(f'''
                        <rect x="{sunrise_x}" y="{margin}" width="{gradient_width}" height="{plot_height}"
                              fill="{colors["daylight"]}" opacity="{opacity}"/>
                    ''')

                    # Add sunrise/sunset lines only for charts 3 days or fewer
                    if self._plot_days <= 3:
                        # Sunrise line
                        elements.append(f'''
                            <line x1="{sunrise_x}" y1="{margin}" x2="{sunrise_x}" y2="{height - margin}"
                                  stroke="{colors["sunrise_line"]}" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.5"/>
                        ''')

                        # Sunrise time label
                        sunrise_label = sunrise.strftime("%I:%M%p").lstrip('0')
                        elements.append(f'''
                            <text x="{sunrise_x + 5}" y="{margin + 15}" text-anchor="start"
                                  font-family="'Courier New', 'Courier', monospace" font-size="9" fill="{colors["sunrise_line"]}">
                                ↑{sunrise_label}
                            </text>
                        ''')

                        # Sunset line
                        elements.append(f'''
                            <line x1="{sunset_x}" y1="{margin}" x2="{sunset_x}" y2="{height - margin}"
                                  stroke="{colors["sunrise_line"]}" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.5"/>
                        ''')

                        # Sunset time label
                        sunset_label = sunset.strftime("%I:%M%p").lstrip('0')
                        elements.append(f'''
                            <text x="{sunset_x - 5}" y="{margin + 15}" text-anchor="end"
                                  font-family="'Courier New', 'Courier', monospace" font-size="9" fill="{colors["sunrise_line"]}">
                                ↓{sunset_label}
                            </text>
                        ''')

        return elements

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

        # Clean minimal color scheme
        if self._dark_mode:
            colors = {
                'background': '#000000' if not self._transparent_background else 'none',
                'tide_line': '#FFFFFF',
                'text': '#FFFFFF',
                'title': '#FFFFFF',
                'high_tide': '#FF6B6B',  # Soft red for high tides
                'low_tide': '#4DABF7',   # Soft blue for low tides
                'daylight': '#FFFFFF',   # White for daylight gradient
                'sunrise_line': '#FFA500',  # Orange for sunrise/sunset
            }
        else:
            colors = {
                'background': '#FFFFFF' if not self._transparent_background else 'none',
                'tide_line': '#000000',
                'text': '#000000',
                'title': '#000000',
                'high_tide': '#DC143C',  # Crimson for high tides
                'low_tide': '#1E90FF',   # Dodger blue for low tides
                'daylight': '#FFE5B4',   # Peach for daylight gradient
                'sunrise_line': '#FF8C00',  # Dark orange for sunrise/sunset
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

        # Add daylight gradient backgrounds
        svg_parts.extend(self._generate_daylight_backgrounds(
            min_time, max_time, margin, height, plot_width, plot_height,
            time_to_x, colors
        ))

        # Generate tide curve path - clean single line
        path_points = []
        for point in curve_points:
            x = time_to_x(point['time'])
            y = height_to_y(point['height'])
            path_points.append(f"{x},{y}")

        if path_points:
            path_data = f"M {path_points[0]} L " + " L ".join(path_points[1:])
            # Single clean tide line
            svg_parts.append(f'<path d="{path_data}" stroke="{colors["tide_line"]}" stroke-width="2" fill="none"/>')

        # Add high/low tide markers with labels
        for extreme in extremes:
            ext_x = time_to_x(extreme['time'])
            ext_y = height_to_y(extreme['height'])
            is_high = extreme['type'] == 'pleamar'

            marker_color = colors['high_tide'] if is_high else colors['low_tide']

            # Draw marker circle
            svg_parts.append(f'<circle cx="{ext_x}" cy="{ext_y}" r="5" fill="{marker_color}"/>')

            # Add label with time (AM/PM) and height
            time_str = extreme['time'].strftime("%I:%M%p").lstrip('0')  # Remove leading zero, add AM/PM
            height_str = f"{extreme['height']:.1f}m"
            label = f"{height_str} @ {time_str}"

            # Position label above for high tides, below for low tides
            label_y = ext_y - 18 if is_high else ext_y + 20

            svg_parts.append(f'''
                <text x="{ext_x}" y="{label_y}" text-anchor="middle" font-family="'Courier New', 'Courier', monospace" font-size="10" fill="{colors["text"]}">
                    {label}
                </text>
            ''')

        # Add current position marker
        if current_height is not None:
            curr_x = time_to_x(current_time)
            curr_y = height_to_y(current_height)

            svg_parts.append(f'<circle cx="{curr_x}" cy="{curr_y}" r="4" fill="{colors["tide_line"]}"/>')

            # Add current time annotation with Courier font - always to the right
            time_str = current_time.strftime("%I:%M%p").lstrip('0')
            curr_label = f'{current_height:.2f}m @ {time_str}'
            svg_parts.append(f'''
                <text x="{curr_x + 10}" y="{curr_y + 4}" text-anchor="start" font-family="'Courier New', 'Courier', monospace" font-size="11" fill="{colors["text"]}">
                    {curr_label}
                </text>
            ''')

        # Add title with Courier font
        if self._plot_days == 1:
            title_text = f"TIDE PREDICTION - {self._name.upper()}"
        else:
            title_text = f"TIDE PREDICTION ({self._plot_days}D) - {self._name.upper()}"

        svg_parts.append(f'''
            <text x="{width/2}" y="25" text-anchor="middle" font-family="'Courier New', 'Courier', monospace" font-size="14" fill="{colors["title"]}">
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
        """Generate axes labels with Courier font."""
        labels = []

        # X-axis (time) labels
        for i in range(5):
            x = margin + (i * plot_width / 4)
            time_ratio = i / 4
            label_time = min_time + (max_time - min_time) * time_ratio
            time_label = label_time.strftime("%H:%M")

            labels.append(f'<text x="{x}" y="{height - margin + 15}" text-anchor="middle" font-family="\'Courier New\', \'Courier\', monospace" font-size="10" fill="{text_color}">{time_label}</text>')

        # Y-axis (height) labels
        for i in range(5):
            y = height - margin - (i * plot_height / 4)
            height_ratio = i / 4
            label_height = min_height + (max_height - min_height) * height_ratio
            height_label = f"{label_height:.1f}m"

            labels.append(f'<text x="{margin - 10}" y="{y + 3}" text-anchor="end" font-family="\'Courier New\', \'Courier\', monospace" font-size="10" fill="{text_color}">{height_label}</text>')

        # Axis labels
        labels.append(f'<text x="{width/2}" y="{height - 10}" text-anchor="middle" font-family="\'Courier New\', \'Courier\', monospace" font-size="10" fill="{text_color}">TIME</text>')
        labels.append(f'''
            <text x="15" y="{height/2}" text-anchor="middle" font-family="'Courier New', 'Courier', monospace" font-size="10" fill="{text_color}"
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
