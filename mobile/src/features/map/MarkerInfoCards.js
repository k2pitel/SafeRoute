import { Linking } from "react-native";

import { InfoCard, InfoText } from "../../ui";

const close = (onClose) => ({ label: "Close", onPress: onClose });

// F8: details for a tapped (official) incident.
export function IncidentInfoCard({ incident, onClose }) {
  return (
    <InfoCard title={incident.type} actions={[close(onClose)]}>
      <InfoText>Date: {new Date(incident.occurred_at).toLocaleString()}</InfoText>
      <InfoText>Info: {incident.description}</InfoText>
    </InfoCard>
  );
}

// F8 + F3: a community report, with how many others have confirmed it and
// a button to confirm it yourself.
export function ReportInfoCard({ report, onConfirm, onClose }) {
  const verified = report.confirmations > 0 ? `${report.confirmations} confirmed` : "Unconfirmed";
  return (
    <InfoCard title={report.type} actions={[{ label: "Confirm", onPress: onConfirm }, close(onClose)]}>
      <InfoText>Date: {new Date(report.occurred_at).toLocaleString()}</InfoText>
      {report.description ? <InfoText>Info: {report.description}</InfoText> : null}
      <InfoText>Community report · {verified}</InfoText>
    </InfoCard>
  );
}

// US-20: what a coloured zone's colour is based on.
export function ZoneInfoCard({ zone, onClose }) {
  const ratio = zone.nationalRate ? zone.rate / zone.nationalRate : null;
  return (
    <InfoCard title={zone.name} actions={[close(onClose)]}>
      <InfoText>
        {zone.rate.toFixed(0)} reported violent offences per 100,000 residents per year
        {ratio ? ` (${ratio.toFixed(1)}× the national ${zone.nationalRate.toFixed(0)})` : ""}.
      </InfoText>
      <InfoText>Tryghedsscore {zone.score.toFixed(1)} / 10 · municipality level</InfoText>
      {zone.period ? <InfoText>Danmarks Statistik, {zone.period}</InfoText> : null}
    </InfoCard>
  );
}

// Details for a tapped crime-news pin, with a link to the article.
export function NewsInfoCard({ item, onClose }) {
  return (
    <InfoCard title={item.title} actions={[{ label: "Open article", onPress: () => Linking.openURL(item.url) }, close(onClose)]}>
      <InfoText>
        {item.source} · {new Date(item.published_at).toLocaleDateString()}
      </InfoText>
    </InfoCard>
  );
}
