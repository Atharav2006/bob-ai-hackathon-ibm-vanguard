import React, { useEffect, useState, useRef } from 'react';
import Map, { Source, Layer, NavigationControl, Popup, MapRef } from 'react-map-gl';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

export const SituationMap: React.FC = () => {
    const mapRef = useRef<MapRef>(null);
    const [zones, setZones] = useState<any[]>([]);
    const [popupInfo, setPopupInfo] = useState<any | null>(null);

    useEffect(() => {
        const fetchMapData = async () => {
            try {
                const response = await fetch(`${API_URL}/map-data`);
                const data = await response.json();
                setZones(data.zones);
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

    // A free dark-themed vector basemap style
    const mapStyle = "mapbox://styles/mapbox/dark-v11";

    const flyToMiami = () => {
        if (mapRef.current) {
            mapRef.current.flyTo({
                center: [-80.19, 25.76],
                zoom: 12,
                pitch: 65,
                bearing: 30,
                duration: 4000,
                essential: true
            });
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '20px 0', background: '#000' }}>
            
            <button 
                onClick={flyToMiami}
                style={{ marginBottom: '15px', background: '#0f62fe', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
            >
                🚀 Zoom to Miami Disaster Zone
            </button>

            <div style={{ height: '500px', width: '100%', maxWidth: '800px', overflow: 'hidden', borderRadius: '8px', border: '1px solid #333', position: 'relative' }}>
                <Map
                    ref={mapRef}
                    mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
                    initialViewState={{
                        longitude: -80.19,
                        latitude: 0,
                        zoom: 1, // Global zoom!
                        pitch: 15,
                        bearing: 0
                    }}
                    projection="globe"
                    mapStyle={mapStyle}
                    interactiveLayerIds={['zones-fill-3d']}
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
                                'fill-extrusion-height': 4000, // 4 km tall walls!
                                'fill-extrusion-base': 0
                            }}
                        />
                    </Source>

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
