import { Linking, Platform } from "react-native";
import * as SecureStore from "expo-secure-store";

import { getCurrentCoordinates } from "../../services/location";

// US-26: emergency contacts live only on this phone (never sent to the
// server, NF11). Sharing opens the phone's own SMS app with the current
// position, so nothing is tracked server-side.
const CONTACTS_KEY = "saferoute_emergency_contacts";

export async function loadContacts() {
  try {
    const json = await SecureStore.getItemAsync(CONTACTS_KEY);
    return json ? JSON.parse(json) : [];
  } catch {
    return [];
  }
}

export async function saveContacts(contacts) {
  await SecureStore.setItemAsync(CONTACTS_KEY, JSON.stringify(contacts));
}

// Opens an SMS to every contact with a map link to where the user is now.
// Returns false when there are no contacts or no position.
export async function sendLocationToContacts(contacts) {
  if (!contacts.length) return false;
  const coords = await getCurrentCoordinates();
  if (!coords) return false;
  const link = `https://www.openstreetmap.org/?mlat=${coords.latitude}&mlon=${coords.longitude}#map=17/${coords.latitude}/${coords.longitude}`;
  const body = encodeURIComponent(`I'm walking home with SafeRoute. My location right now: ${link}`);
  const numbers = contacts.map((c) => c.phone.replace(/\s+/g, "")).join(Platform.OS === "ios" ? "," : ";");
  const separator = Platform.OS === "ios" ? "&" : "?";
  await Linking.openURL(`sms:${numbers}${separator}body=${body}`);
  return true;
}
