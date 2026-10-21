import { createContext, useContext, useEffect, useState } from "react";
import * as SecureStore from "expo-secure-store";

import { api, setAuthToken } from "../../services/api";

const TOKEN_KEY = "saferoute_auth_token";
const USER_KEY = "saferoute_auth_user";

// Reports require login (see backend/app/routers/auth.py) so they can't be
// faked/spammed anonymously. This holds the signed-in user + session token
// app-wide, persisted in SecureStore so login survives an app restart.
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      const [token, userJson] = await Promise.all([
        SecureStore.getItemAsync(TOKEN_KEY),
        SecureStore.getItemAsync(USER_KEY),
      ]);
      if (token && userJson) {
        setAuthToken(token);
        setUser(JSON.parse(userJson));
      }
      setReady(true);
    })();
  }, []);

  const persistSession = async (token, nextUser) => {
    setAuthToken(token);
    setUser(nextUser);
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(nextUser));
  };

  const login = async (email, password) => {
    const { access_token, user: loggedInUser } = await api.login(email, password);
    await persistSession(access_token, loggedInUser);
  };

  const signup = async (email, password) => {
    const { access_token, user: newUser } = await api.signup(email, password);
    await persistSession(access_token, newUser);
  };

  const logout = async () => {
    setAuthToken(null);
    setUser(null);
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
  };

  return (
    <AuthContext.Provider value={{ user, ready, login, signup, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
