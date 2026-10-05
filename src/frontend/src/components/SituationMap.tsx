import React, { useEffect, useState } from 'react';
import Map, { Source, Layer, NavigationControl, Marker, Popup } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

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

    // A free raster basemap style (OpenStreetMap) converted for MapLibre WebGL
    const mapStyle = {
        version: 8 as const,
        sources: {
            "osm": {
                type: "raster" as const,
                tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
                tileSize: 256,
                attribution: "&copy; OpenStreetMap Contributors"
            }
        },
        layers: [
            {
                id: "osm-tiles",
                type: "raster" as const,
                source: "osm",
                minzoom: 0,
                maxzoom: 19
            }
        ]
    };

    return (
        <div style={{ height: '500px', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
            <Map
                initialViewState={{
                    longitude: 1.5,
                    latitude: 1.5,
                    zoom: 6,
                    pitch: 45 // 3D Tilt!
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
                        id="zones-fill"
                        type="fill"
                        paint={{
                            'fill-color': '#ff0000',
                            'fill-opacity': 0.4
                        }}
                    />
                    {/* @ts-ignore */}
                    <Layer 
                        id="zones-line"
                        type="line"
                        paint={{
                            'line-color': '#990000',
                            'line-width': 2
                        }}
                    />
                </Source>

                {/* Render Resources as HTML Markers on top of WebGL */}
                {resources.map((res) => {
                    if (res.geojson.type === "Point") {
                        const [longitude, latitude] = res.geojson.coordinates;
                        return (
                            <Marker 
                                key={res.id} 
                                longitude={longitude} 
                                latitude={latitude}
                                anchor="bottom"
                                onClick={e => {
                                    e.originalEvent.stopPropagation();
                                    setPopupInfo({ lngLat: { lng: longitude, lat: latitude }, name: res.name, type: `Resource (${res.mode})` });
                                }}
                            >
                                <div style={{ fontSize: '24px', cursor: 'pointer' }}>📍</div>
                            </Marker>
                        );
                    }
                    return null;
                })}

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
    );
};
