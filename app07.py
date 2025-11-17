
from flask import Flask, request, jsonify, render_template, session
from datetime import datetime, timedelta
import sqlite3
import threading
import time
import pytz
import re
 
# Import shared objects from extension
from extension import db, colombo_tz

# Import auth blueprint and decorator
from auth import auth_bp, login_required

app = Flask(__name__)

# IMPORTANT: Set a secret key for session management
app.secret_key = 'ae672b758d988238d431925a099a315f5f54d3849a47b43e751e5d162b02fbec'  # CHANGE THIS!
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=200)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///plant_monitoring.db?check_same_thread=False"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=200)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True,
    'connect_args': {
        'check_same_thread': False,
        'timeout': 30
    }
}

# Initialize db with app
db.init_app(app)

# Register authentication blueprint
app.register_blueprint(auth_bp)
# Plant configuration - Your actual plant-unit mapping
PLANT_CONFIG = {
    1: 1,   # PTA
    2: 2,   # BGD
    3: 2,   # THA
    4: 2,   # KLP
    5: 3,   # GRU
    6: 2,   # WW1
    7: 2,   # WW2
    8: 2,   # GAM
    9: 3,   # WEG
    10: 2,  # FAV
    11: 1,  # BC1
    12: 2,  # BC2
    13: 2,  # NAK
}

PLANT_NAMES = {
    1: "PTA", 2: "BGD", 3: "THA", 4: "KLP", 5: "GRU",
    6: "WW1", 7: "WW2", 8: "GAM", 9: "WEG", 10: "FAV",
    11: "BC1", 12: "BC2", 13: "NAK",
}

# Reverse mapping for plant name to ID
PLANT_NAME_TO_ID = {v.lower(): k for k, v in PLANT_NAMES.items()}

# Helper function to get current Colombo time
def get_colombo_time():
    return datetime.now(colombo_tz)

# Helper function to convert UTC to Colombo time
def utc_to_colombo(utc_dt):
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(colombo_tz)

# Enhanced table model for comprehensive ESP32 data
def create_plant_table(plant_id,plant_name):
    class_name = f'Plant{plant_id}Data'
    table_name = f'plant_{plant_name}_data'
    
    attrs = {
        '__tablename__': table_name,
        'id': db.Column(db.Integer, primary_key=True),
        'unit_id': db.Column(db.Integer, nullable=False),
        
        # Power measurements
        'power': db.Column(db.Float, nullable=True),
        
        # Current measurements (3-phase)
        'current_l1': db.Column(db.Float, nullable=True),
        'current_l2': db.Column(db.Float, nullable=True),
        'current_l3': db.Column(db.Float, nullable=True),
        'current_avg': db.Column(db.Float, nullable=True),
        
        # Voltage measurements (3-phase)
        'voltage_l12': db.Column(db.Float, nullable=True),
        'voltage_l23': db.Column(db.Float, nullable=True),
        'voltage_l13': db.Column(db.Float, nullable=True),
        'voltage_avg': db.Column(db.Float, nullable=True),
        
        # Energy and runtime
        'energy': db.Column(db.Float, nullable=True),
        'runtime': db.Column(db.Float, nullable=True),
        
        # Additional calculated fields
        'power_factor': db.Column(db.Float, nullable=True),
        'efficiency': db.Column(db.Float, nullable=True),
        
        'timestamp': db.Column(db.DateTime, default=datetime.utcnow)
    }
    
    return type(class_name, (db.Model,), attrs)

# Create all plant table models
PLANT_TABLES = {}
for plant_id,plant_name in PLANT_NAMES.items():
    PLANT_TABLES[plant_id] = create_plant_table(plant_id,plant_name)

# Create all tables
with app.app_context():
    db.create_all()

def parse_esp32_data(json_data):
    """
    Parse ESP32-style JSON data and extract plant_id, unit_id, and measurements
    Expected format: {plantname}_u{unit_id}_{parameter}: value
    """
    parsed_units = {}
    
    # Regular expression to match the ESP32 data format
    pattern = r'([a-zA-Z0-9]+)_u(\d+)_(.+)'
    
    for key, value in json_data.items():
        match = re.match(pattern, key)
        if match:
            plant_name = match.group(1).lower()
            unit_id = int(match.group(2))
            parameter = match.group(3)
            
            # Get plant_id from plant name
            plant_id = PLANT_NAME_TO_ID.get(plant_name)
            if plant_id is None:
                continue
                
            # Initialize unit data if not exists
            unit_key = (plant_id, unit_id)
            if unit_key not in parsed_units:
                parsed_units[unit_key] = {
                    'plant_id': plant_id,
                    'unit_id': unit_id,
                }
            
            # Map parameters to database fields
            try:
                value = float(value)
                if parameter == 'power':
                    parsed_units[unit_key]['power'] = value
                elif parameter == 'current_L1':
                    parsed_units[unit_key]['current_l1'] = value
                elif parameter == 'current_L2':
                    parsed_units[unit_key]['current_l2'] = value
                elif parameter == 'current_L3':
                    parsed_units[unit_key]['current_l3'] = value
                elif parameter == 'voltage_L12':
                    parsed_units[unit_key]['voltage_l12'] = value
                elif parameter == 'voltage_L23':
                    parsed_units[unit_key]['voltage_l23'] = value
                elif parameter == 'voltage_L13':
                    parsed_units[unit_key]['voltage_l13'] = value
                elif parameter == 'energy':
                    parsed_units[unit_key]['energy'] = value
                elif parameter == 'runtime':
                    parsed_units[unit_key]['runtime'] = value
                    
            except (ValueError, TypeError):
                continue
    
    # Calculate averages for units that have the data
    for unit_data in parsed_units.values():
        # Calculate average current
        currents = [unit_data.get('current_l1'), unit_data.get('current_l2'), unit_data.get('current_l3')]
        valid_currents = [c for c in currents if c is not None]
        if valid_currents:
            unit_data['current_avg'] = sum(valid_currents) / len(valid_currents)
        
        # Calculate average voltage
        voltages = [unit_data.get('voltage_l12'), unit_data.get('voltage_l23'), unit_data.get('voltage_l13')]
        valid_voltages = [v for v in voltages if v is not None]
        if valid_voltages:
            unit_data['voltage_avg'] = sum(valid_voltages) / len(valid_voltages)
    
    return list(parsed_units.values())
def cleanup_old_data():
    """
    Runs every 24 hours and deletes records older than 7 days
    """
    while True:
        try:
            with app.app_context():
                # Calculate cutoff date (7 days ago)
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                
                print(f"[{datetime.now()}] Running cleanup for data older than {cutoff_date}")
                
                # Delete old data from each plant table
                for plant_id, PlantTable in PLANT_TABLES.items():
                    # Count records to be deleted
                    old_records = PlantTable.query.filter(
                        PlantTable.timestamp < cutoff_date
                    ).count()
                    
                    if old_records > 0:
                        # Delete old records
                        PlantTable.query.filter(
                            PlantTable.timestamp < cutoff_date
                        ).delete()
                        
                        db.session.commit()
                        print(f"  ✓ Plant {plant_id}: Deleted {old_records} old records")
                    else:
                        print(f"  ✓ Plant {plant_id}: No old records to delete")
                
                print("Cleanup completed successfully!")
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            db.session.rollback()
        
        # Wait 24 hours before next cleanup
        time.sleep(24 * 60 * 60)  # 86400 seconds = 24 hours

# Start cleanup thread when app starts
def start_cleanup_thread():
    cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
    cleanup_thread.start()
    print("✓ Auto-cleanup thread started (runs every 24 hours)")

# API endpoint for ESP32 data submission (No authentication required for IoT devices)
@app.route("/data", methods=["POST"])
def receive_data():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON data provided"}), 400
        
        # Parse ESP32 data format
        parsed_units = parse_esp32_data(data)
        
        if not parsed_units:
            return jsonify({"status": "error", "message": "No valid unit data found in request"}), 400
        
        stored_records = []
        
        # Process each unit's data
        for unit_data in parsed_units:
            plant_id = unit_data['plant_id']
            unit_id = unit_data['unit_id']
            
            # Validate plant exists in configuration
            if plant_id not in PLANT_CONFIG:
                continue
                
            # Validate unit exists for this plant
            if unit_id < 1 or unit_id > PLANT_CONFIG[plant_id]:
                continue
            
            # Get the appropriate table for this plant
            PlantTable = PLANT_TABLES[plant_id]
            
            # Create new record with all available data
            new_data = PlantTable(
                unit_id=unit_id,
                power=unit_data.get('power'),
                current_l1=unit_data.get('current_l1'),
                current_l2=unit_data.get('current_l2'),
                current_l3=unit_data.get('current_l3'),
                current_avg=unit_data.get('current_avg'),
                voltage_l12=unit_data.get('voltage_l12'),
                voltage_l23=unit_data.get('voltage_l23'),
                voltage_l13=unit_data.get('voltage_l13'),
                voltage_avg=unit_data.get('voltage_avg'),
                energy=unit_data.get('energy'),
                runtime=unit_data.get('runtime')
            )
            
            # Store data with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    db.session.add(new_data)
                    db.session.commit()
                    
                    # Convert timestamp to Colombo timezone for response
                    local_timestamp = utc_to_colombo(new_data.timestamp)
                    
                    stored_records.append({
                        "plant_id": plant_id,
                        "unit_id": unit_id,
                        "id": new_data.id,
                        "power": unit_data.get('power'),
                        "timestamp": local_timestamp.strftime("%Y-%m-%d %H:%M:%S") if local_timestamp else "Unknown"
                    })
                    break
                    
                except Exception as db_error:
                    db.session.rollback()
                    if attempt == max_retries - 1:
                        raise db_error
                    time.sleep(0.1 * (attempt + 1))
        
        if stored_records:
            return jsonify({
                "status": "success", 
                "stored_records": len(stored_records),
                "records": stored_records
            })
        else:
            return jsonify({"status": "error", "message": "No valid data could be stored"}), 400
                
    except Exception as e:
        db.session.rollback()
        print(f"Error in receive_data: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Master Dashboard - Main page (Login Required)
@app.route("/")
@login_required
def master_dashboard():
    try:
        # Get latest data from all plants (within last 2 minutes for online check)
        time_limit = datetime.utcnow() - timedelta(minutes=2)
        
        plant_data = {}
        total_power = 0
        total_running_units = 0  # Changed from total_online_units
        total_standby_units = 0  # NEW
        total_offline_units = 0  # NEW
        active_plants = 0
        
        for plant_id, unit_count in PLANT_CONFIG.items():
            PlantTable = PLANT_TABLES[plant_id]
            
            # Get latest data for each unit in this plant
            units_data = []
            plant_power = 0
            plant_running_units = 0  # Changed from plant_online_units
            plant_standby_units = 0  # NEW
            plant_offline_units = 0  # NEW
            
            for unit_id in range(1, unit_count + 1):
                latest_record = PlantTable.query.filter_by(unit_id=unit_id)\
                                               .filter(PlantTable.timestamp >= time_limit)\
                                               .order_by(PlantTable.timestamp.desc())\
                                               .first()
                
                if latest_record:
                    local_timestamp = utc_to_colombo(latest_record.timestamp)
                    
                    power = latest_record.power or 0
                    current_avg = latest_record.current_avg or 0
                    voltage_avg = latest_record.voltage_avg or 0
                    
                    # Check if unit is in STANDBY mode
                    # Standby = sending data but all values are 0
                    is_standby = (power == 0 and current_avg == 0 and voltage_avg == 0)
                    
                    if is_standby:
                        # STANDBY: Connected but not running
                        status = 'standby'
                        plant_standby_units += 1
                    else:
                        # ONLINE/RUNNING: Connected and running
                        status = 'running'
                        plant_power += power
                        plant_running_units += 1
                        
                    units_data.append({
                        'unit_id': unit_id,
                        'power': power,
                        'current_avg': current_avg,
                        'voltage_avg': voltage_avg,
                        'energy': latest_record.energy or 0,
                        'runtime': latest_record.runtime or 0,
                        'timestamp': local_timestamp,
                        'status': status,  # 'online' or 'standby'
                        'online': True,    # Still communicating
                        'standby': is_standby  # True if standby
                    })
                    #plant_power += (latest_record.power or 0)
                    #plant_online_units += 1
                else:
                    # OFFLINE: No data received in last 2 minutes
                    plant_offline_units += 1
                    
                    units_data.append({
                        'unit_id': unit_id,
                        'power': 0,
                        'current_avg': 0,
                        'voltage_avg': 0,
                        'energy': 0,
                        'runtime': 0,
                        'timestamp': None,
                        'status': 'offline',
                        'online': False,
                        'standby': False
                    })
            
            if plant_running_units > 0 :
                active_plants += 1
            
            plant_data[plant_id] = {
                'plant_id': plant_id,
                'total_units': unit_count,
                'running_units': plant_running_units,  # Units actually generating power
                'standby_units': plant_standby_units,  # Units connected but idle
                'offline_units': plant_offline_units,  # Units not communicating
                'online_units': plant_running_units + plant_standby_units,  # Total communicating
                'total_power': plant_power,
                'units': units_data
            }
            
            total_power += plant_power
            total_running_units += plant_running_units
            total_standby_units += plant_standby_units
            total_offline_units += plant_offline_units
        
        return render_template(
            "master_dashboard08.html",
            plant_data=plant_data,
            total_power=total_power,
            total_running_units=total_running_units,      # NEW
            total_standby_units=total_standby_units,      # NEW
            total_offline_units=total_offline_units,      # NEW
            total_online_units=total_running_units + total_standby_units,        # For backward compatibility
            total_units=sum(PLANT_CONFIG.values()),
            active_plants=active_plants,
            plant_config=PLANT_CONFIG,
            current_time=get_colombo_time(),
            plant_names=PLANT_NAMES,
            username=session.get('username', 'User')
        )
        
    except Exception as e:
        print(f"Error in master_dashboard: {str(e)}")
        return jsonify({"status": "error", "message": "Database error"}), 500

# API to get live data for master dashboard (Login Required)
@app.route("/api/master/live")
@login_required
def get_master_live_data():
    try:
        time_limit = datetime.utcnow() - timedelta(minutes=2)
        
        plant_data = {}
        total_power = 0
        total_running_units = 0
        total_standby_units = 0
        total_offline_units = 0
        active_plants = 0
        
        for plant_id, unit_count in PLANT_CONFIG.items():
            PlantTable = PLANT_TABLES[plant_id]
            
            units_data = []
            plant_power = 0
            plant_running_units = 0
            plant_standby_units = 0
            plant_offline_units = 0
            
            for unit_id in range(1, unit_count + 1):
                latest_record = PlantTable.query.filter_by(unit_id=unit_id)\
                                               .filter(PlantTable.timestamp >= time_limit)\
                                               .order_by(PlantTable.timestamp.desc())\
                                               .first()
                
                if latest_record:
                    local_timestamp = utc_to_colombo(latest_record.timestamp)
                    
                    power = latest_record.power or 0
                    current_avg = latest_record.current_avg or 0
                    voltage_avg = latest_record.voltage_avg or 0
                    
                    # Check if in standby mode
                    is_standby = (power == 0 and current_avg == 0 and voltage_avg == 0)
                    
                    if is_standby:
                        status = 'standby'
                        plant_standby_units += 1 
                    else:
                        status = 'online'
                        plant_running_units += 1 
                        plant_power += power
                        
                    units_data.append({
                        'unit_id': unit_id,
                        'power': round(power, 2),
                        'current_avg': round(current_avg, 2),
                        'voltage_avg': round(voltage_avg, 2),
                        'current_l1': round(latest_record.current_l1 or 0, 2),
                        'current_l2': round(latest_record.current_l2 or 0, 2),
                        'current_l3': round(latest_record.current_l3 or 0, 2),
                        'voltage_l12': round(latest_record.voltage_l12 or 0, 2),
                        'voltage_l23': round(latest_record.voltage_l23 or 0, 2),
                        'voltage_l13': round(latest_record.voltage_l13 or 0, 2),
                        'energy': round(latest_record.energy or 0, 2),
                        'runtime': round(latest_record.runtime or 0, 2),
                        'timestamp': local_timestamp.strftime("%H:%M:%S") if local_timestamp else '--:--:--',
                        'status': status,
                        'online': True,
                        'standby': is_standby
                    })
                    #plant_power += (latest_record.power or 0)
                    #plant_online_units += 1
                else:
                    plant_offline_units += 1
                    
                    units_data.append({
                        'unit_id': unit_id,
                        'power': 0,
                        'current_avg': 0,
                        'voltage_avg': 0,
                        'current_l1': 0,
                        'current_l2': 0,
                        'current_l3': 0,
                        'voltage_l12': 0,
                        'voltage_l23': 0,
                        'voltage_l13': 0,
                        'energy': 0,
                        'runtime': 0,
                        'timestamp': '--:--:--',
                        'status': 'offline',
                        'online': False,
                        'standby': False
                    })
            
            if plant_running_units > 0:
                active_plants += 1
            
            plant_data[plant_id] = {
                'plant_id': plant_id,
                'total_units': unit_count,
                'running_units': plant_running_units,
                'standby_units': plant_standby_units,
                'offline_units': plant_offline_units,
                'online_units': plant_running_units + plant_standby_units,
                'total_power': round(plant_power, 2),
                'units': units_data
            }
            
            total_power += plant_power
            total_running_units += plant_running_units
            total_standby_units += plant_standby_units
            total_offline_units += plant_offline_units
        
        return jsonify({
            'plant_data': plant_data,
            'total_power': round(total_power, 2),
            'total_running_units': total_running_units,
            'total_standby_units': total_standby_units,
            'total_offline_units': total_offline_units,
            'total_online_units': total_running_units + total_standby_units,  # For backward compatibility
            'total_units': sum(PLANT_CONFIG.values()),
            'active_plants': active_plants,
            'timestamp': get_colombo_time().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"Error in get_master_live_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API to get historical data for a specific plant (Login Required)
@app.route("/api/plant/<int:plant_id>/history")
@login_required
def get_plant_history(plant_id):
    try:
        if plant_id not in PLANT_CONFIG:
            return jsonify({"error": f"Plant {plant_id} not found"}), 404
            
        PlantTable = PLANT_TABLES[plant_id]
        
        # Get last 5 hours of data
        time_limit = datetime.utcnow() - timedelta(hours=7)
        current_time = datetime.utcnow()
        records = PlantTable.query.filter(PlantTable.timestamp >= time_limit)\
                                 .order_by(PlantTable.timestamp.asc()).all()
        
        # Group by 5-minute intervals
        time_groups = {}
        for record in records:
            local_timestamp = utc_to_colombo(record.timestamp)
            if local_timestamp is None:
                continue
                
            # Round to nearest 5-minute interval
            time_key = local_timestamp.replace(second=0, microsecond=0, tzinfo=None)
            minute = time_key.minute
            time_key = time_key.replace(minute=minute - (minute % 1))
            
            if time_key not in time_groups:
                time_groups[time_key] = {}
            
            unit_id = record.unit_id
            if unit_id not in time_groups[time_key]:
                time_groups[time_key][unit_id] = record.power or 0
            else:
                time_groups[time_key][unit_id] = record.power or 0
                
         # Fill ALL time intervals (including missing ones)
        local_time_limit = utc_to_colombo(time_limit)
        local_current_time = utc_to_colombo(current_time)
        
        if local_time_limit and local_current_time:
            local_time_limit = local_time_limit.replace(second=0, microsecond=0, tzinfo=None)
            local_current_time = local_current_time.replace(second=0, microsecond=0, tzinfo=None)
            
            # Round to 5-minute boundaries
            start_time = local_time_limit.replace(minute=local_time_limit.minute - (local_time_limit.minute % 5))
            end_time = local_current_time.replace(minute=local_current_time.minute - (local_current_time.minute % 5))
            
            # Generate all intervals
            current_interval = start_time
            while current_interval <= end_time:
                if current_interval not in time_groups:
                    time_groups[current_interval] = {}  # Empty = offline
                current_interval += timedelta(minutes=1)
        
        
        # Calculate total plant power for each time interval
        chart_data = {
            'labels': [],
            'power': [],
            'current': [],
            'voltage': []
        }
        
        for time_key in sorted(time_groups.keys()):
            units_in_interval = time_groups[time_key]
            total_plant_power = sum(units_in_interval.values()) if units_in_interval else 0
            
            chart_data['labels'].append(time_key.strftime("%H:%M"))
            chart_data['power'].append(round(total_plant_power, 2))
        
        return jsonify(chart_data)
        
    except Exception as e:
        print(f"Error in get_plant_history: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

# Plant Detail Page (Login Required)
@app.route("/plant/<int:plant_id>")
@login_required
def plant_detail_page(plant_id):
    try:
        if plant_id not in PLANT_CONFIG:
            return render_template("error.html", error=f"Plant {plant_id} not found"), 404
            
        PlantTable = PLANT_TABLES[plant_id]
        time_limit = datetime.utcnow() - timedelta(minutes=2)
        unit_count = PLANT_CONFIG[plant_id]
        
        units_data = []
        plant_power = 0
        running_units = 0
        standby_units = 0
        offline_units = 0
        
        for unit_id in range(1, unit_count + 1):
            latest_record = PlantTable.query.filter_by(unit_id=unit_id)\
                                           .filter(PlantTable.timestamp >= time_limit)\
                                           .order_by(PlantTable.timestamp.desc())\
                                           .first()
            
            if latest_record:
                local_timestamp = utc_to_colombo(latest_record.timestamp)
                
                power = latest_record.power or 0
                current_avg = latest_record.current_avg or 0
                voltage_avg = latest_record.voltage_avg or 0
                
                # Check if in standby
                is_standby = (power == 0 and current_avg == 0 and voltage_avg == 0)
                
                if is_standby:
                    status = 'standby'
                    standby_units += 1
                else:
                    status = 'online'
                    plant_power += power
                    running_units += 1
                
                unit_data = {
                    'unit_id': unit_id,
                    'power': round(power, 2),
                    'current_avg': round(current_avg, 2),
                    'voltage_avg': round(voltage_avg, 2),
                    'current_l1': round(latest_record.current_l1 or 0, 2),
                    'current_l2': round(latest_record.current_l2 or 0, 2),
                    'current_l3': round(latest_record.current_l3 or 0, 2),
                    'voltage_l12': round(latest_record.voltage_l12 or 0, 2),
                    'voltage_l23': round(latest_record.voltage_l23 or 0, 2),
                    'voltage_l13': round(latest_record.voltage_l13 or 0, 2),
                    'energy': round(latest_record.energy or 0, 2),
                    'runtime': round(latest_record.runtime or 0, 2),
                    'timestamp': local_timestamp.strftime("%Y-%m-%d %H:%M:%S") if local_timestamp else 'No data',
                    'status': status,
                    'online': True,
                    'standby': is_standby
                }
            else:
                offline_units += 1
                
                unit_data = {
                    'unit_id': unit_id,
                    'power': 0,
                    'current_avg': 0,
                    'voltage_avg': 0,
                    'current_l1': 0,
                    'current_l2': 0,
                    'current_l3': 0,
                    'voltage_l12': 0,
                    'voltage_l23': 0,
                    'voltage_l13': 0,
                    'energy': 0,
                    'runtime': 0,
                    'timestamp': 'No data',
                    'status': 'offline',
                    'online': False,
                    'standby': False
                }
            
            units_data.append(unit_data)
            
        plant_data = {
            'plant_id': plant_id,
            'total_units': unit_count,
            'running_units': running_units,
            'standby_units': standby_units,
            'offline_units': offline_units,
            'online_units': running_units + standby_units,
            'total_power': round(plant_power, 2),
            'average_power_per_unit': round(plant_power / running_units, 2) if running_units > 0 else 0,
            'units': units_data,
        }
        return render_template(
            "plant_details05.html",
            plant_data=plant_data,
            current_time=get_colombo_time(),
            plant_names=PLANT_NAMES,
            username=session.get('username', 'User')
        )
        
    except Exception as e:
        print(f"Error in plant_detail_page: {str(e)}")
        return render_template("error.html", error="Database error"), 500
    
# API to get detailed plant information (Login Required)
@app.route("/api/plant/<int:plant_id>/details")
@login_required
def get_plant_details(plant_id):
    try:
        if plant_id not in PLANT_CONFIG:
            return jsonify({"error": f"Plant {plant_id} not found"}), 404
            
        PlantTable = PLANT_TABLES[plant_id]
        time_limit = datetime.utcnow() - timedelta(minutes=2)
        unit_count = PLANT_CONFIG[plant_id]
        
        units_data = []
        plant_power = 0
        online_units = 0
        
        for unit_id in range(1, unit_count + 1):
            latest_record = PlantTable.query.filter_by(unit_id=unit_id)\
                                           .filter(PlantTable.timestamp >= time_limit)\
                                           .order_by(PlantTable.timestamp.desc())\
                                           .first()
            
            if latest_record:
                local_timestamp = utc_to_colombo(latest_record.timestamp)
                
                units_data = []
        plant_power = 0
        running_units = 0
        standby_units = 0
        offline_units = 0
        
        for unit_id in range(1, unit_count + 1):
            latest_record = PlantTable.query.filter_by(unit_id=unit_id)\
                                           .filter(PlantTable.timestamp >= time_limit)\
                                           .order_by(PlantTable.timestamp.desc())\
                                           .first()
            
            if latest_record:
                local_timestamp = utc_to_colombo(latest_record.timestamp)
                
                power = latest_record.power or 0
                current_avg = latest_record.current_avg or 0
                voltage_avg = latest_record.voltage_avg or 0
                
                is_standby = (power == 0 and current_avg == 0 and voltage_avg == 0)
                
                if is_standby:
                    status = 'standby'
                    standby_units += 1
                else:
                    status = 'online'
                    plant_power += power
                    running_units += 1
                
                unit_data = {
                    'unit_id': unit_id,
                    'power': round(power, 2),
                    'current_avg': round(current_avg, 2),
                    'voltage_avg': round(voltage_avg, 2),
                    'current_l1': round(latest_record.current_l1 or 0, 2),
                    'current_l2': round(latest_record.current_l2 or 0, 2),
                    'current_l3': round(latest_record.current_l3 or 0, 2),
                    'voltage_l12': round(latest_record.voltage_l12 or 0, 2),
                    'voltage_l23': round(latest_record.voltage_l23 or 0, 2),
                    'voltage_l13': round(latest_record.voltage_l13 or 0, 2),
                    'energy': round(latest_record.energy or 0, 2),
                    'runtime': round(latest_record.runtime or 0, 2),
                    'timestamp': local_timestamp.strftime("%Y-%m-%d %H:%M:%S") if local_timestamp else 'No data',
                    'status': status,
                    'online': True,
                    'standby': is_standby
                }
            else:
                offline_units += 1
                
                unit_data = {
                    'unit_id': unit_id,
                    'power': 0,
                    'current_avg': 0,
                    'voltage_avg': 0,
                    'current_l1': 0,
                    'current_l2': 0,
                    'current_l3': 0,
                    'voltage_l12': 0,
                    'voltage_l23': 0,
                    'voltage_l13': 0,
                    'energy': 0,
                    'runtime': 0,
                    'timestamp': 'No data',
                    'status': 'offline',
                    'online': False,
                    'standby': False
                }
            
            units_data.append(unit_data)
                    
        return jsonify({
            'plant_id': plant_id,
            'total_units': unit_count,
            'running_units': running_units,
            'standby_units': standby_units,
            'offline_units': offline_units,
            'online_units': running_units + standby_units,
            'total_power': round(plant_power, 2),
            'average_power_per_unit': round(plant_power / running_units, 2) if running_units > 0 else 0,
            'units': units_data,
            'timestamp': get_colombo_time().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        print(f"Error in get_plant_details: {str(e)}")
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    print("🏭 Enhanced Plant Monitoring System with Authentication Starting...")
    print("=" * 60)
    print("Plant Configuration:")
    total_units = 0
    for plant_id, unit_count in PLANT_CONFIG.items():
        plant_name = PLANT_NAMES.get(plant_id, f"Plant{plant_id}")
        print(f"  Plant {plant_id} ({plant_name}): {unit_count} units")
        total_units += unit_count
    print(f"Total Units Across All Plants: {total_units}")
    print(f"Current Colombo Time: {get_colombo_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("\nDatabase Schema Enhanced with:")
    print("  ✅ User Authentication System")
    print("  ✅ Registration & Login")
    print("  ✅ Session Management")
    print("  ✅ 3-Phase Current Measurements (L1, L2, L3)")
    print("  ✅ 3-Phase Voltage Measurements (L12, L23, L13)")
    print("  ✅ Power, Energy, and Runtime")
    print("  ✅ Calculated Averages")
    print("  ✅ ESP32 JSON Format Parser")
    print("\nAccess Points:")
    print("  🔐 Login: http://localhost:5000/login")
    print("  📝 Register: http://localhost:5000/register")
    print("  🏭 Dashboard: http://localhost:5000/ (requires login)")
    print("=" * 60)
    
    print("\n🧹 Starting auto-cleanup thread...")
    cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
    cleanup_thread.start()
    print("✓ Cleanup thread started (runs every 24 hours)")
    print("  - Deletes records older than 7 days")
    print("  - First cleanup in 24 hours\n")
    
    print("🚀 Starting Flask server...")
    print("=" * 60 + "\n")
    
    app.run(port=5000, debug=True, threaded=True)

