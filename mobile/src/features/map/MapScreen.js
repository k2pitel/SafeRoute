import { useEffect, useRef, useState } from "react";
import { Alert, StyleSheet, Text, View, TouchableOpacity } from "react-native";
import MapView, { Marker, Polygon, Polyline } from "react-native-maps";
import { Ionicons } from "@expo/vector-icons";

import { api } from "../../services/api";
import { getCurrentCoordinates } from "../../services/location";
import { radius, spacing, useTheme, useThemedStyles } from "../../theme";
import { BottomSheet, PeriodPicker, TextButton } from "../../ui";
import { useAuth } from "../auth/AuthContext";
import AuthPromptModal from "../auth/AuthPromptModal";
import ReportModal from "../reports/ReportModal";
import { useActiveRoute } from "../routes/ActiveRouteContext";
import RoutePanel from "../routes/RoutePanel";
import { useSettings } from "../settings/SettingsContext";
import { useWalkMonitor } from "../walk/useWalkMonitor";
import { DARK_MAP_STYLE } from "./darkMapStyle";
import { jitterCoordinate } from "./jitterCoordinate";
import MapLegend from "./MapLegend";
import { IncidentInfoCard, NewsInfoCard, ReportInfoCard, ZoneInfoCard } from "./MarkerInfoCards";
import { useMapData } from "./useMapData";

// Centred so all of Denmark (incl. Bornholm) is visible on open, since news
// pins are scattered nationwide rather than local.
const DENMARK_REGION = { latitude: 55.95, longitude: 10.8, latitudeDelta: 4.2, longitudeDelta: 8.5 };
const ZOOMED_IN_DELTA = 0.02;
const SAFE_ROUTE_THRESHOLD = 6.5; // route drawn green at/above this tryghedsscore
const ROUTE_EDGE_PADDING = { top: 80, right: 60, bottom: 80, left: 60 };
// US-18: report pins are drawn 30–80 m off their true position, so a pin
// never points at the reporter's exact doorstep. Deterministic per report.
const REPORT_JITTER = { minDegrees: 0.0003, spreadDegrees: 0.0004 };

// Kort: colour-coded zones (F7), marker details (F8), confirming reports
// (F3) + UC1 (route panel, drawn route, walk monitoring F5) + UC2 (report button).
export default function MapScreen() {
  const { colors, dark } = useTheme();
  const styles = useThemedStyles(makeStyles);
  const mapRef = useRef(null);
  const [region, setRegion] = useState(DENMARK_REGION);
  const [selected, setSelected] = useState(null); // { kind: "incident" | "report" | "news" | "zone", item }
  const [reportCoordinate, setReportCoordinate] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const afterLogin = useRef(null); // what to continue with once AuthPromptModal succeeds
  const { activeRoute, walking } = useActiveRoute();
  const { user } = useAuth();
  const { settings, updateSetting } = useSettings();
  // Year range for the crime-news pins: null = every year in the archive.
  const [newsPeriod, setNewsPeriod] = useState(null);
  const [newsYears, setNewsYears] = useState(null); // { min_year, max_year }
  const [showPeriodSheet, setShowPeriodSheet] = useState(false);
  useEffect(() => {
    api.getNewsYears().then((y) => y.min_year && setNewsYears(y)).catch(() => {});
  }, []);
  const effectiveNewsPeriod =
    newsPeriod || (newsYears ? { from: newsYears.min_year, to: newsYears.max_year } : null);
  const newsPeriodLabel = newsPeriod
    ? newsPeriod.from === newsPeriod.to
      ? String(newsPeriod.from)
      : `${newsPeriod.from}–${newsPeriod.to}`
    : "All years";

  const { incidents, reports, zones, newsPins, addReport, replaceReport } = useMapData(region, effectiveNewsPeriod);
  const visibleReports = settings.showReports ? reports : [];
  useWalkMonitor(activeRoute, walking);

  // Hide/show community report pins; remembered across restarts (SettingsContext).
  const toggleReports = () => {
    if (settings.showReports && selected?.kind === "report") setSelected(null);
    updateSetting("showReports", !settings.showReports);
  };

  // Login-gated actions (UC2 extension 3a): run now if signed in, otherwise
  // after a successful login — never if the user cancels.
  const requireLogin = (action) => {
    if (user) {
      action();
    } else {
      afterLogin.current = action;
      setShowAuthModal(true);
    }
  };

  useEffect(() => {
    getCurrentCoordinates().then((coords) => {
      if (coords) setRegion((r) => ({ ...r, ...coords }));
    });
  }, []);

  const goToMyLocation = async () => {
    const coords = await getCurrentCoordinates();
    if (!coords) return;
    const next = { ...coords, latitudeDelta: ZOOMED_IN_DELTA, longitudeDelta: ZOOMED_IN_DELTA };
    setRegion(next);
    mapRef.current?.animateToRegion(next, 400);
  };

  // UC2: the position is fetched before login is checked (step 2 before 3),
  // so the report is placed where the user is. Reporting requires login —
  // if the user isn't signed in, prompt for that first and only open the
  // report form once auth succeeds (extension 3a).
  const handleReportPress = async () => {
    const coords = await getCurrentCoordinates();
    if (!coords) {
      // UC2 extension 2a: a report needs the user's position.
      Alert.alert("Location needed", "SafeRoute places a report at your current location. Allow location access to report.");
      return;
    }
    setReportCoordinate(coords);
    requireLogin(() => setShowReportModal(true));
  };

  // F3: confirm another user's report.
  const handleConfirm = (report) =>
    requireLogin(async () => {
      try {
        const updated = await api.confirmReport(report.id);
        replaceReport(updated);
        setSelected({ kind: "report", item: updated });
      } catch (e) {
        Alert.alert("Could not confirm", e.message);
      }
    });

  const handleSubmitReport = async (payload) => {
    addReport(await api.submitReport(payload));
    setShowReportModal(false);
  };

  // Draw the route picked in RoutePanel (GeoJSON is [lon, lat]) and fit the camera to it.
  const routeCoords = activeRoute?.option.geometry.coordinates.map(([longitude, latitude]) => ({
    latitude,
    longitude,
  }));

  useEffect(() => {
    if (routeCoords && routeCoords.length > 1 && mapRef.current) {
      mapRef.current.fitToCoordinates(routeCoords, { edgePadding: ROUTE_EDGE_PADDING, animated: true });
    }
  }, [activeRoute]); // eslint-disable-line react-hooks/exhaustive-deps

  const routeColor = activeRoute?.option.safety_score >= SAFE_ROUTE_THRESHOLD ? colors.safe : colors.danger;

  const zonePeriod = zones.find((z) => z.info?.period)?.info.period;

  const legendEntries = [
    zones.some((z) => z.label === "unsafe") && { color: colors.zone.unsafe.stroke, label: "Unsafe area" },
    zones.some((z) => z.label === "mixed") && { color: colors.zone.mixed.stroke, label: "Mixed area" },
    newsPins.length > 0 && { color: colors.marker.news, label: `Crime news (${newsPeriodLabel})` },
    visibleReports.length > 0 && { color: colors.marker.report, label: "Community report" },
  ].filter(Boolean);

  return (
    <View style={styles.container}>
      <RoutePanel />

      <View style={styles.mapWrapper}>
        <MapView
          ref={mapRef}
          style={styles.map}
          initialRegion={region}
          onRegionChangeComplete={setRegion}
          showsUserLocation
          userInterfaceStyle={dark ? "dark" : "light"}
          customMapStyle={dark ? DARK_MAP_STYLE : []}
        >
          {zones.map((zone) => (
            <Polygon
              key={`zone-${zone.id}`}
              coordinates={zone.polygon}
              fillColor={colors.zone[zone.label].fill}
              strokeColor={colors.zone[zone.label].stroke}
              strokeWidth={1}
              tappable
              onPress={() => setSelected({ kind: "zone", item: zone.info })}
            />
          ))}

          {incidents.map((incident) => (
            <Marker
              key={`incident-${incident.id}`}
              coordinate={{ latitude: incident.latitude, longitude: incident.longitude }}
              pinColor={colors.marker.incident}
              onPress={() => setSelected({ kind: "incident", item: incident })}
            />
          ))}

          {newsPins.map((item) => (
            <Marker
              key={`news-${item.url}`}
              coordinate={jitterCoordinate(item.url, item.latitude, item.longitude)}
              pinColor={colors.marker.news}
              onPress={() => setSelected({ kind: "news", item })}
            />
          ))}

          {visibleReports.map((report) => (
            <Marker
              key={`report-${report.id}`}
              coordinate={jitterCoordinate(`report-${report.id}`, report.latitude, report.longitude, REPORT_JITTER)}
              pinColor={colors.marker.report}
              onPress={() => setSelected({ kind: "report", item: report })}
            />
          ))}

          {routeCoords && <Polyline coordinates={routeCoords} strokeColor={routeColor} strokeWidth={5} />}
          {activeRoute?.destination && (
            <Marker
              coordinate={{
                latitude: activeRoute.destination.latitude,
                longitude: activeRoute.destination.longitude,
              }}
              pinColor={colors.marker.destination}
              title={activeRoute.destination.label}
            />
          )}
        </MapView>

        <MapLegend entries={legendEntries} footnote={zonePeriod ? `Crime data ${zonePeriod}` : null} />

        {/* Year range for the news pins */}
        <TouchableOpacity style={styles.periodChip} onPress={() => setShowPeriodSheet(true)}>
          <Ionicons name="calendar-outline" size={15} color={colors.primary} />
          <Text style={styles.periodChipText}>
            {newsPeriodLabel} · {newsPins.length} pins
          </Text>
          <Ionicons name="chevron-down" size={14} color={colors.textMuted} />
        </TouchableOpacity>

        <BottomSheet
          visible={showPeriodSheet}
          onClose={() => setShowPeriodSheet(false)}
          title="Crime news on the map"
          subtitle={
            newsYears
              ? `Show news pins from a range of years (${newsYears.min_year}–${newsYears.max_year} available).`
              : "Show news pins from a range of years."
          }
        >
          <PeriodPicker
            value={newsPeriod}
            range={newsYears}
            onChange={setNewsPeriod}
            defaultLabel="All years"
            note={`${newsPins.length} placed articles shown`}
          />
          <TextButton label="Done" onPress={() => setShowPeriodSheet(false)} style={styles.periodDone} />
        </BottomSheet>

        {/* DP-02: routing, search and map features derive from OSM data (ODbL). */}
        <Text style={styles.attribution}>© OpenStreetMap contributors</Text>

        <TouchableOpacity style={[styles.fab, styles.reportFab]} onPress={handleReportPress}>
          <Ionicons name="warning" size={22} color={colors.onPrimary} />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.fab, styles.reportsToggleFab]}
          onPress={toggleReports}
          accessibilityRole="button"
          accessibilityLabel={settings.showReports ? "Hide community reports" : "Show community reports"}
        >
          <Ionicons name={settings.showReports ? "eye" : "eye-off"} size={22} color={colors.primary} />
        </TouchableOpacity>

        <TouchableOpacity style={[styles.fab, styles.locateFab]} onPress={goToMyLocation}>
          <Ionicons name="locate" size={24} color={colors.primary} />
        </TouchableOpacity>

        {selected?.kind === "incident" && (
          <IncidentInfoCard incident={selected.item} onClose={() => setSelected(null)} />
        )}
        {selected?.kind === "report" && (
          <ReportInfoCard
            report={selected.item}
            onConfirm={() => handleConfirm(selected.item)}
            onClose={() => setSelected(null)}
          />
        )}
        {selected?.kind === "news" && <NewsInfoCard item={selected.item} onClose={() => setSelected(null)} />}
        {selected?.kind === "zone" && <ZoneInfoCard zone={selected.item} onClose={() => setSelected(null)} />}
      </View>

      <AuthPromptModal
        visible={showAuthModal}
        onClose={() => {
          afterLogin.current = null;
          setShowAuthModal(false);
        }}
        onAuthenticated={() => {
          setShowAuthModal(false);
          afterLogin.current?.();
          afterLogin.current = null;
        }}
      />

      <ReportModal
        visible={showReportModal}
        coordinate={reportCoordinate}
        onClose={() => setShowReportModal(false)}
        onSubmit={handleSubmitReport}
      />
    </View>
  );
}

const makeStyles = ({ colors, elevation }) =>
  StyleSheet.create({
    container: { flex: 1 },
    mapWrapper: { flex: 1 },
    map: { flex: 1 },
    fab: {
      position: "absolute",
      right: spacing.lg,
      width: 50,
      height: 50,
      borderRadius: radius.fab,
      alignItems: "center",
      justifyContent: "center",
      ...elevation,
    },
    locateFab: { bottom: 100, backgroundColor: colors.surface },
    reportFab: { bottom: 160, backgroundColor: colors.danger },
    reportsToggleFab: { bottom: 220, backgroundColor: colors.surface },
    periodChip: {
      position: "absolute",
      top: spacing.md,
      left: spacing.md,
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      backgroundColor: colors.surface,
      borderRadius: radius.pill,
      paddingVertical: 7,
      paddingHorizontal: 12,
      ...elevation,
    },
    periodChipText: { color: colors.text, fontWeight: "600", fontSize: 13 },
    periodDone: { marginTop: spacing.lg },
    attribution: {
      position: "absolute",
      bottom: 4,
      alignSelf: "center",
      fontSize: 10,
      color: colors.textMuted,
      backgroundColor: colors.surface,
      opacity: 0.85,
      paddingHorizontal: 6,
      borderRadius: 4,
      overflow: "hidden",
    },
  });
