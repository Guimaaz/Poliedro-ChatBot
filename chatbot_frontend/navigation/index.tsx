import React from 'react';
import { createNativeStackNavigator, NativeStackNavigationProp } from '@react-navigation/native-stack';
import { NavigationContainer } from '@react-navigation/native';
import LoginScreen from '../app/(tabs)/LoginScreen';
import ChatScreen from '../app/(tabs)/chatbotScreen';

const Stack = createNativeStackNavigator();

export type RootStackParamList = {
  LoginScreen: undefined;
  ChatScreen: undefined;
  // Adicione outras telas e seus parâmetros aqui
};

export type RootStackNavigationProp = NativeStackNavigationProp<RootStackParamList>;
export type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'LoginScreen'>;
export type ChatScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'ChatScreen'>;

const AppNavigator = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="LoginScreen"
        screenOptions={{
          headerStyle: {
            backgroundColor: '#4B3D3D',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
            fontSize: 20,
          },
          contentStyle: {
            backgroundColor: '#e0e0e0',
          },
        }}
      >
        <Stack.Screen name="LoginScreen" component={LoginScreen} options={{ title: 'Área de Login' }} />
        <Stack.Screen name="ChatScreen" component={ChatScreen} options={{ title: 'Popoli Chat Poliedro' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;