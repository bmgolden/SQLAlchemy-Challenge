import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the table
Station = Base.classes.station
Measurement = Base.classes.measurement

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"  # tmin, tmax, tavg for specified start date
    )

# Route for Precipitation Data
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(bind=engine)

    # Most recent date
    most_recent_date = dt.datetime(2017, 8, 23)

    # Calculate the date one year from the last date in data set.
    one_year = most_recent_date - dt.timedelta(days=366)

    measurement_data = session.query(
        Measurement.date, Measurement.prcp
    ).filter(Measurement.date >= one_year).all()

    # Precipitation dictionary
    precipitation_dict = {date: prcp for date, prcp in measurement_data}

    session.close()

    return jsonify(precipitation_dict)

# Route for Station Data
@app.route("/api/v1.0/stations")
def stations():
    # Create session from Python to the DB
    session = Session(bind=engine)

    stations_list_names = session.query(
        Measurement.station
    ).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()

    # Extracting the station names from the query result
    station_names = [station[0] for station in stations_list_names]

    session.close()
    return jsonify(station_names)


# Route for Temperature Observations
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(bind=engine)

    most_active_station = session.query(
        Measurement.station,
        func.min(Measurement.tobs),
        func.max(Measurement.tobs),
        func.avg(Measurement.tobs)
    ).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()

    if most_active_station:
        most_active_station_id = most_active_station[0]  # Extract the station ID

        # Calculate the date 12 months ago from most recent
        # Most recent date
        first_measurement = dt.datetime(2017, 8, 23)

        # Calculate the date one year from the last date in data set.
        one_year_ago = first_measurement - dt.timedelta(days=366)

        temperature_data = session.query(
            Measurement.date, Measurement.tobs
        ).filter(
            Measurement.station == most_active_station_id,
            Measurement.date >= one_year_ago
        ).all()

        # Extract the temperature values for plotting
        temperatures = [temp.tobs for temp in temperature_data]

        session.close()
        return jsonify(temperatures)


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start, end=None):
    # Create our session (link) from Python to the DB
    session = Session(bind=engine)

    if end:
        # If both start and end dates are provided
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    else:
        # If only the start date is provided
        results = session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs)
        ).filter(Measurement.date >= start).all()

    # Close the session
    session.close()

    # Extract the result and structure the response
    temp_data = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temp_data)


if __name__ == '__main__':
    app.run(debug=True)