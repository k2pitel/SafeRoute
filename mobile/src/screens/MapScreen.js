import { useEffect, useRef, useState } from "react";
import { StyleSheet, View, Text, TouchableOpacity, Linking } from "react-native";
import MapView, { Marker, Polyline } from "react-native-maps";
import * as Location from "expo-location";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../services/api";
import { useActiveRoute } from "../context/ActiveRouteContext";
import { useAuth } from "../context/AuthContext";
import AuthPromptModal from "../components/AuthPromptModal";
import ReportModal from "../components/ReportModal";

// News pins are geocoded to a fixed town/district center (see backend
// app/danish_places.py) rather than the actual crime scene, so every story
// about the same place shares one exact coordinate — with years of
// archived news that stacks dozens of pins on a single point and only the
// topmost one is tappable. Spread each pin deterministically (same URL
// always lands in the same spot) around its town center so every story
// gets its own tappable position while still reading as "near that town".
function jitterCoordinate(seed, latitude, longitude) {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  const angle = ((hash % 360) * Math.PI) / 180;
  const radiusDegrees = 0.004 + (Math.abs(hash) % 100 / 100) * 0.006; // ~450m-1.1km spread
  return {
    latitude: latitude + radiusDegrees * Math.cos(angle),
    longitude: longitude + (radiusDegrees * Math.sin(angle)) / Math.cos((latitude * Math.PI) / 180),
  };
}

// README > Mobile App — Pages > 1. Home / Map Page
// Shows crime pins (X = Crimes) and the current fast-vs-safe route
// comparison drawn on the map. Safety zones are disabled for now.
export default function MapScreen() {
  const mapRef = useRef(null);
  const [region, setRegion] = useState({
    latitude: 55.95, // centered so all of Denmark (incl. Bornholm) is visible on open,
    longitude: 10.8, // since news pins are scattered nationwide rather than local
    latitudeDelta: 4.2,
    longitudeDelta: 8.5,
  });
  const [incidents, setIncidents] = useState([]);
  const [newsPins, setNewsPins] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [selectedNews, setSelectedNews] = useState(null);
  const [reportCoordinate, setReportCoordinate] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const { activeRoute } = useActiveRoute();
  const { user } = useAuth();

  // Crime news is nationwide, not tied to the current map viewport, so it's
  // fetched once rather than re-fetched on every region change. Pulls every
  // archived year (not just "latest") so the map isn't dominated by
  // this-year's news alone — see api.getNewsAllYears.
  useEffect(() => {
    api
      .getNewsAllYears()
      .then((items) => setNewsPins(items.filter((item) => item.latitude != null)))
      .catch(() => setNewsPins([]));
  }, []);

  const goToMyLocation = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return;
    const loc = await Location.getCurrentPositionAsync({});
    const next = {
      latitude: loc.coords.latitude,
      longitude: loc.coords.longitude,
      latitudeDelta: 0.02,
      longitudeDelta: 0.02,
    };
    setRegion(next);
    mapRef.current?.animateToRegion(next, 400);
  };

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === "granted") {
        const loc = await Location.getCurrentPositionAsync({});
        setRegion((r) => ({ ...r, latitude: loc.coords.latitude, longitude: loc.coords.longitude }));
      }
    })();
  }, []);

  useEffect(() => {
    const bbox = [
      region.longitude - region.longitudeDelta,
      region.latitude - region.latitudeDelta,
      region.longitude + region.longitudeDelta,
      region.latitude + region.latitudeDelta,
    ].join(",");

    api.getIncidents(bbox).then(setIncidents).catch(() => setIncidents([]));
    api.getReports(bbox).then(setReports).catch(() => setReports([]));
  }, [region.latitude, region.longitude]);

  // Reporting requires login — if the user isn't signed in, prompt for
  // that first and only open the report form once auth succeeds.
  const handleReportPress = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return;
    const loc = await Location.getCurrentPositionAsync({});
    setReportCoordinate({ latitude: loc.coords.latitude, longitude: loc.coords.longitude });
    if (user) setShowReportModal(true);
    else setShowAuthModal(true);
  };

  const handleSubmitReport = async (payload) => {
    const created = await api.submitReport(payload);
    setReports((prev) => [...prev, created]);
    setShowReportModal(false);
  };

  // Draw the route picked on the Route tab, and fit the camera to it.
  const routeCoords = activeRoute?.option.geometry.coordinates.map(([longitude, latitude]) => ({
    latitude,
    longitude,
  }));

  useEffect(() => {
    if (routeCoords && routeCoords.length > 1 && mapRef.current) {
      mapRef.current.fitToCoordinates(routeCoords, {
        edgePadding: { top: 80, right: 60, bottom: 80, left: 60 },
        animated: true,
      });
    }
  }, [activeRoute]); // eslint-disable-line react-hooks/exhaustive-deps

  const routeColor = activeRoute && activeRoute.option.safety_score >= 6.5 ? "#0EA47A" : "#E5484D";

  return (
    <View style={styles.container}>
      <MapView ref={mapRef} style={styles.map} initialRegion={region} showsUserLocation>
        {incidents.map((incident) => (
          <Marker
            key={`incident-${incident.id}`}
            coordinate={{ latitude: incident.latitude, longitude: incident.longitude }}
            pinColor="red"
            onPress={() => {
              setSelectedNews(null);
              setSelectedIncident(incident);
            }}
          />
        ))}

        {newsPins.map((item) => (
          <Marker
            key={`news-${item.url}`}
            coordinate={jitterCoordinate(item.url, item.latitude, item.longitude)}
            pinColor="blue"
            onPress={() => {
              setSelectedIncident(null);
              setSelectedNews(item);
            }}
          />
        ))}

        {reports.map((report) => (
          <Marker
            key={`report-${report.id}`}
            coordinate={{ latitude: report.latitude, longitude: report.longitude }}
            pinColor="orange"
            onPress={() => {
              setSelectedNews(null);
              setSelectedIncident(report);
            }}
          />
        ))}

        {routeCoords && <Polyline coordinates={routeCoords} strokeColor={routeColor} strokeWidth={5} />}
        {activeRoute?.destination && (
          <Marker
            coordinate={{
              latitude: activeRoute.destination.latitude,
              longitude: activeRoute.destination.longitude,
            }}
            pinColor="#007AFF"
            title={activeRoute.destination.label}
          />
        )}
      </MapView>

      {(newsPins.length > 0 || reports.length > 0) && (
        <View style={styles.legend}>
          {newsPins.length > 0 && (
            <View style={styles.legendRow}>
              <View style={[styles.legendDot, { backgroundColor: "blue" }]} />
              <Text style={styles.legendText}>Crime news</Text>
            </View>
          )}
          {reports.length > 0 && (
            <View style={styles.legendRow}>
              <View style={[styles.legendDot, { backgroundColor: "orange" }]} />
              <Text style={styles.legendText}>Community report</Text>
            </View>
          )}
        </View>
      )}

      <TouchableOpacity style={styles.reportFab} onPress={handleReportPress}>
        <Ionicons name="warning" size={22} color="white" />
      </TouchableOpacity>

      <TouchableOpacity style={styles.locateFab} onPress={goToMyLocation}>
        <Ionicons name="locate" size={24} color="#007AFF" />
      </TouchableOpacity>

      <AuthPromptModal
        visible={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthenticated={() => {
          setShowAuthModal(false);
          setShowReportModal(true);
        }}
      />

      <ReportModal
        visible={showReportModal}
        coordinate={reportCoordinate}
        onClose={() => setShowReportModal(false)}
        onSubmit={handleSubmitReport}
      />

      {activeRoute && (
        <View style={styles.routeBanner}>
          <Text style={styles.routeBannerText}>
            {Math.round(activeRoute.option.duration_minutes)} min · Safety: {activeRoute.option.safety_label} (
            {activeRoute.option.safety_score.toFixed(1)}/10)
          </Text>
        </View>
      )}

      {selectedIncident && (
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>{selectedIncident.type}</Text>
          <Text>Date: {new Date(selectedIncident.occurred_at).toLocaleString()}</Text>
          <Text>Info: {selectedIncident.description}</Text>
          <TouchableOpacity onPress={() => setSelectedIncident(null)}>
            <Text style={styles.close}>Close</Text>
          </TouchableOpacity>
        </View>
      )}

      {selectedNews && (
        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>{selectedNews.title}</Text>
          <Text>
            {selectedNews.source} · {new Date(selectedNews.published_at).toLocaleDateString()}
          </Text>
          <View style={styles.newsActions}>
            <TouchableOpacity onPress={() => Linking.openURL(selectedNews.url)}>
              <Text style={styles.close}>Open article</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setSelectedNews(null)}>
              <Text style={styles.close}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  locateFab: {
    position: "absolute",
    right: 16,
    bottom: 100,
    backgroundColor: "white",
    borderRadius: 24,
    padding: 10,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  reportFab: {
    position: "absolute",
    right: 16,
    bottom: 160,
    backgroundColor: "#E5484D",
    borderRadius: 24,
    padding: 12,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  routeBanner: {
    position: "absolute",
    top: 12,
    left: 20,
    right: 20,
    backgroundColor: "white",
    borderRadius: 10,
    padding: 10,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  routeBannerText: { textAlign: "center", fontWeight: "600" },
  legend: {
    position: "absolute",
    left: 16,
    bottom: 100,
    backgroundColor: "white",
    borderRadius: 10,
    padding: 10,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  legendRow: { flexDirection: "row", alignItems: "center", marginVertical: 2 },
  legendDot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  legendText: { fontSize: 12, color: "#333" },
  infoCard: {
    position: "absolute",
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: "white",
    borderRadius: 12,
    padding: 16,
    elevation: 4,
    shadowColor: "#000",
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  infoTitle: { fontWeight: "bold", fontSize: 16, marginBottom: 4, textTransform: "capitalize" },
  close: { color: "#007AFF", marginTop: 8 },
  newsActions: { flexDirection: "row", justifyContent: "space-between" },
});
