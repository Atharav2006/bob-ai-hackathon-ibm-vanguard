import React, { useEffect, useState, useRef } from "react";
import Map, { Source, Layer, NavigationControl, Popup, MapRef } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useAuth } from "../AuthContext";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

export const SituationMap: React.FC = () => {
    const { token, incidentId } = useAuth();
    const mapRef = useRef<MapRef>(null);
    const [zones, setZones] = useState<any[]>([]);
    const [popupInfo, setPopupInfo] = useState<any | null>(null);

    useEffect(() => {
        const fetchMapData = async () => {
            if (!token || !incidentId) return;
            try {
                const response = await fetch(`${API_URL}/map-data`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "X-Incident-ID": incidentId
                    }
                });
                const data = await response.json();
                setZones(data.zones || []);
            } catch (err) {
                console.error("Failed to load map data", err);
            }
        };
        fetchMapData();
    }, [token, incidentId]);

    const zonesGeoJSON = {
        type: "FeatureCollection",
        features: zones.map(z => ({
            type: "Feature",
            geometry: z.geojson || null,
            properties: { id: z.id, name: z.name }
        }))
    };

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
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "100%", padding: "20px 0", background: "#000" }}>
            
            <button 
                onClick={flyToMiami}
                style={{ marginBottom: "15px", background: "#0f62fe", color: "white", padding: "10px 20px", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: "bold" }}
            >
                Zoom to Disaster Zone
            </button>

            <div style={{ height: "500px", width: "100%", maxWidth: "800px", overflow: "hidden", borderRadius: "8px", border: "1px solid #333", position: "relative" }}>
                <Map
                    ref={mapRef}
                    mapboxAccessToken={import.meta.env.VITE_MAPBOX_TOKEN}
                    initialViewState={{
                        longitude: -80.19,
                        latitude: 0,
                        zoom: 1,
                        pitch: 15,
                        bearing: 0
                    }}
                    projection={{ name: "globe" }}
                    mapStyle={mapStyle}
                    interactiveLayerIds={["zones-fill-3d"]}
                    onClick={(event) => {
                        if (event.features && event.features.length > 0) {
                            const feature = event.features[0];
                            setPopupInfo({
                                lngLat: event.lngLat,
                                name: feature.properties?.name,
                                type: "Zone"
                            });
                        }
                    }}
                >
                    <NavigationControl position="top-right" />

                    {/* @ts-ignore */}
                    <Source id="zones-source" type="geojson" data={zonesGeoJSON}>
                        {/* @ts-ignore */}
                        <Layer 
                            id="zones-fill-3d"
                            type="fill-extrusion"
                            paint={{
                                "fill-extrusion-color": "#ff0000",
                                "fill-extrusion-opacity": 0.6,
                                "fill-extrusion-height": 4000,
                                "fill-extrusion-base": 0
                            }}
                        />
                    </Source>

                    {popupInfo && (
                        <Popup
                            longitude={popupInfo.lngLat.lng}
                            latitude={popupInfo.lngLat.lat}
                            anchor="top"
                            onClose={() => setPopupInfo(null)}
                        >
                            <div style={{ color: "black", padding: "5px" }}>
                                <strong>{popupInfo.type}:</strong> {popupInfo.name}
                            </div>
                        </Popup>
                    )}
                </Map>
            </div>
        </div>
    );
};

