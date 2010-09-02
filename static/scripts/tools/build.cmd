IF dummy==dummy%1 (
python build.sahana.py
) ELSE (
python build.sahana.py %1
@echo !! Action Required !!
@echo Be sure to search OpenLayers.js output file for 'style.css' and amend path to '../../styles/gis/style.css'
)
