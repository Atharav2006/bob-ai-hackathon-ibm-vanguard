import React, { useEffect, useState } from 'react';
import Map, { Source, Layer, NavigationControl, Marker, Popup } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

export const SituationMap: React.FC = () => {
    const [zones, setZones] = useState<any[]>([]);
    const [resources, setResources] = useState<any[]>([]);
    const [popupInfo, setPopupInfo] = useState<any | null>(null);

    useEffect(() => {
        const fetchMapData = async () => {
            try {
                const response = await fetch(`${API_URL}/map-data`);
                const data = await response.json();
                setZones(data.zones);
                setResources(data.resources);
            } catch (err) {
                console.error("Failed to load map data", err);
            }
        };
        fetchMapData();
    }, []);

    // Create a valid GeoJSON FeatureCollection for the Zones
    const zonesGeoJSON = {
        type: "FeatureCollection",
        features: zones.map(z => ({
            type: "Feature",
            geometry: z.geojson,
            properties: { id: z.id, name: z.name }
        }))
    };

    // A free dark-themed vector basemap style (Carto Dark Matter)
    const mapStyle = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

    return (
        <div style={{ display: 'flex', justifyContent: 'center', width: '100%', padding: '20px 0' }}>
            <div style={{ height: '500px', width: '500px', borderRadius: '50%', overflow: 'hidden', border: '5px solid #0f62fe', boxShadow: '0 0 20px rgba(15, 98, 254, 0.4)' }}>
                <Map
                    initialViewState={{
                        longitude: -80.19,
                        latitude: 25.76,
                        zoom: 12,
                        pitch: 60 // Extreme 3D Tilt!
                    }}
                    mapStyle={mapStyle}
                    mapLib={maplibregl}
                    interactiveLayerIds={['zones-fill']}
                    onClick={(event) => {
                        if (event.features && event.features.length > 0) {
                            const feature = event.features[0];
                            setPopupInfo({
                                lngLat: event.lngLat,
                                name: feature.properties?.name,
                                type: 'Zone'
                            });
                        }
                    }}
                >
                    <NavigationControl position="top-right" />

                    {/* Render Zones via WebGL GeoJSON Source */}
                    {/* @ts-ignore */}
                    <Source id="zones-source" type="geojson" data={zonesGeoJSON}>
                        {/* @ts-ignore */}
                        <Layer 
                            id="zones-fill-3d"
                            type="fill-extrusion"
                            paint={{
                                'fill-extrusion-color': '#ff0000',
                                'fill-extrusion-opacity': 0.6,
                                'fill-extrusion-height': 800, // 800 meters tall!
                                'fill-extrusion-base': 0
                            }}
                        />
                    </Source>

                    {/* Resources/Points have been removed per user request */}

                {/* Popups */}
                {popupInfo && (
                    <Popup
                        longitude={popupInfo.lngLat.lng}
                        latitude={popupInfo.lngLat.lat}
                        anchor="top"
                        onClose={() => setPopupInfo(null)}
                    >
                        <div style={{ color: 'black', padding: '5px' }}>
                            <strong>{popupInfo.type}:</strong> {popupInfo.name}
                        </div>
                    </Popup>
                )}
            </Map>
            </div>
        </div>
    );
};
