import { Linking, Text } from "react-native";

import { InfoCard } from "../../ui";

const close = (onClose) => ({ label: "Close", onPress: onClose });

// F8: details for a tapped (official) incident.
export function IncidentInfoCard({ incident, onClose }) {
  return (
    <InfoCard title={incident.type} actions={[close(onClose)]}>
      <Text>Date: {new Date(incident.occurred_at).toLocaleString()}</Text>
      <Text>Info: {incident.description}</Text>
    </InfoCard>
  );
}

// F8 + F3: a community report, with how many others have confirmed it and
// a button to confirm it yourself.
export function ReportInfoCard({ report, onConfirm, onClose }) {
  const verified = report.confirmations > 0 ? `${report.confirmations} confirmed` : "Unconfirmed";
  return (
    <InfoCard title={report.type} actions={[{ label: "Confirm", onPress: onConfirm }, close(onClose)]}>
      <Text>Date: {new Date(report.occurred_at).toLocaleString()}</Text>
      {report.description ? <Text>Info: {report.description}</Text> : null}
      <Text>Community report · {verified}</Text>
    </InfoCard>
  );
}

// Details for a tapped crime-news pin, with a link to the article.
export function NewsInfoCard({ item, onClose }) {
  return (
    <InfoCard title={item.title} actions={[{ label: "Open article", onPress: () => Linking.openURL(item.url) }, close(onClose)]}>
      <Text>
        {item.source} · {new Date(item.published_at).toLocaleDateString()}
      </Text>
    </InfoCard>
  );
}
