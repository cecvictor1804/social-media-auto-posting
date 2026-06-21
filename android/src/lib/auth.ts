import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "smap_access_token";

export const getToken = () => SecureStore.getItemAsync(TOKEN_KEY);
export const setToken = (t: string) => SecureStore.setItemAsync(TOKEN_KEY, t);
export const clearToken = () => SecureStore.deleteItemAsync(TOKEN_KEY);
