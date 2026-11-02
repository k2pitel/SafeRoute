import { Modal, ScrollView, StyleSheet, Text, View } from "react-native";

import { radius, spacing, useThemedStyles } from "../theme";

// Modal that slides up from the bottom over a dimmed backdrop — the shell
// of every form (login, incident report). Content scrolls if it's tall.
export default function BottomSheet({ visible, onClose, title, subtitle, children }) {
  const styles = useThemedStyles(makeStyles);
  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <ScrollView style={styles.sheet} contentContainerStyle={styles.content}>
          <View style={styles.grabber} />
          {title && <Text style={styles.title}>{title}</Text>}
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          {children}
        </ScrollView>
      </View>
    </Modal>
  );
}

const makeStyles = ({ colors, typography }) =>
  StyleSheet.create({
    backdrop: { flex: 1, backgroundColor: colors.backdrop, justifyContent: "flex-end" },
    sheet: {
      backgroundColor: colors.surface,
      borderTopLeftRadius: radius.sheet,
      borderTopRightRadius: radius.sheet,
      padding: spacing.xl,
      paddingTop: spacing.md,
      maxHeight: "80%",
      flexGrow: 0,
    },
    content: { paddingBottom: spacing.md },
    grabber: {
      alignSelf: "center",
      width: 40,
      height: 4,
      borderRadius: 2,
      backgroundColor: colors.border,
      marginBottom: spacing.lg,
    },
    title: { ...typography.title, marginBottom: spacing.xs },
    subtitle: { color: colors.textMuted, ...typography.caption, marginBottom: spacing.lg },
  });
