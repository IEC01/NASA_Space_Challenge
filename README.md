# Yaxanal Sunu Mbaaye – Crop Rotation Decision-Support Assistant

NASA Space Apps Challenge Dakar 2026 · Team AgriSpace Dakar

A Streamlit tool that helps farmers in Senegal choose crop rotations. It combines NASA Earth observations
(NASA POWER, MODIS NDVI) with soil texture (ISRIC SoilGrids), crop characteristics and the farmer's priorities,
ranks three-season rotations, and replays chosen rotations over 20 years of NASA climate data.

## Run it

```
pip install -r requirements.txt
streamlit run app.py
```

## Data sources

- NASA POWER (rainfall, temperature, root-zone soil wetness): https://power.larc.nasa.gov
- NASA MODIS MOD13Q1 NDVI via ORNL DAAC: https://modis.ornl.gov
- ISRIC SoilGrids (soil texture, non-NASA): https://soilgrids.org
- OpenStreetMap (map tiles)

## Use of AI

The code in this repository was written with the help of a generative AI assistant (Claude, Anthropic),
then run and tested by the team. [Describe what the team reviewed or changed.]

## Limits

Crop parameters and scoring weights are first-version approximations inspired by FAO-56 / FAO-33 and have not
been validated in the field. NASA POWER has a resolution of about 50 km.
