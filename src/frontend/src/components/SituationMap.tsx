import React, { useEffect, useState, useRef } from 'react';
import Globe from 'react-globe.gl';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

export const SituationMap: React.FC = () => {
    const globeRef = useRef<any>(null);
    const [zones, setZones] = useState<any[]>([]);

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

    // On load, set the initial view to Miami, but DO NOT rotate.
    useEffect(() => {
        if (globeRef.current) {
            // Wait a tick for Globe to initialize
            setTimeout(() => {
                globeRef.current.pointOfView({ lat: 25.76, lng: -80.19, altitude: 2 }, 0);
            }, 500);
        }
    }, [globeRef.current]);

    const zonesGeoJSON = zones.map(z => ({
        type: "Feature",
        geometry: z.geojson,
        properties: { id: z.id, name: z.name }
    }));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '20px 0', background: '#000' }}>
            
            <button 
                onClick={() => {
                    if (globeRef.current) {
                        globeRef.current.pointOfView({ lat: 25.76, lng: -80.19, altitude: 0.1 }, 4000);
                    }
                }}
                style={{ marginBottom: '15px', background: '#0f62fe', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
            >
                🚀 Zoom to Miami Disaster Zone
            </button>

            <div style={{ height: '500px', width: '800px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #333', position: 'relative', cursor: 'grab' }}>
                <Globe
                    ref={globeRef}
                    width={800}
                    height={500}
                    globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
                    bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
                    backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
                    polygonsData={zonesGeoJSON}
                    polygonGeoJsonGeometry={(d: any) => d.geometry}
                    polygonCapColor={() => 'rgba(255, 0, 0, 0.8)'}
                    polygonSideColor={() => 'rgba(255, 0, 0, 0.4)'}
                    polygonAltitude={0.05}
                />
            </div>
        </div>
    );
};
