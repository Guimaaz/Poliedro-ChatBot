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
      <Stack.Navigator initialRouteName="LoginScreen">
        <Stack.Screen name="LoginScreen" component={LoginScreen} />
        <Stack.Screen name="ChatScreen" component={ChatScreen} />
        {/* Adicione outras telas aqui */}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;