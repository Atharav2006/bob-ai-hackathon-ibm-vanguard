import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polygon, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet's default icon paths
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export const SituationMap: React.FC = () => {
    const [zones, setZones] = useState<any[]>([]);
    const [resources, setResources] = useState<any[]>([]);

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

    // PostGIS geometries are generally Lon/Lat, but Leaflet uses Lat/Lon!
    // We must reverse the coordinates for Polygons and Points.
    const reverseCoords = (coords: number[][]) => coords.map(c => [c[1], c[0]]);

    return (
        <div style={{ height: '500px', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
            <MapContainer center={[1.5, 1.5]} zoom={6} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                {/* Render Zones */}
                {zones.map((zone) => {
                    if (zone.geojson.type === "Polygon") {
                        const positions = reverseCoords(zone.geojson.coordinates[0]);
                        return (
                            <Polygon key={zone.id} positions={positions as any} pathOptions={{ color: 'red', fillColor: '#ff0000', fillOpacity: 0.3 }}>
                                <Popup>
                                    <strong>Zone:</strong> {zone.name} <br/>
                                </Popup>
                            </Polygon>
                        );
                    }
                    return null;
                })}

                {/* Render Resources */}
                {resources.map((res) => {
                    if (res.geojson.type === "Point") {
                        const pos = [res.geojson.coordinates[1], res.geojson.coordinates[0]];
                        return (
                            <Marker key={res.id} position={pos as any}>
                                <Popup>
                                    <strong>Resource:</strong> {res.name} <br/>
                                    <strong>Mode:</strong> {res.mode}
                                </Popup>
                            </Marker>
                        );
                    }
                    return null;
                })}
            </MapContainer>
        </div>
    );
};
