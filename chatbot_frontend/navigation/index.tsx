import React from 'react';
import { createNativeStackNavigator, NativeStackNavigationProp } from '@react-navigation/native-stack';
import { NavigationContainer } from '@react-navigation/native';
import LoginScreen from '../app/(tabs)/LoginScreen';
import ChatScreen from '../app/(tabs)/chatbotScreen';
import RegisterScreen from '../app/(tabs)/RegisterScreen';
import AdminHomeScreen from '../app/(tabs)/AdminMenuScreen';
import AdminPedidosScreen from '../app/(tabs)/AdminPedidosScreen';
import AdminCardapioScreen from '../app/(tabs)/AdminCardapioScreen';
import AdminClientesScreen from '../app/(tabs)/AdminClienteScreen';

const Stack = createNativeStackNavigator();

export type RootStackParamList = {
  LoginScreen: undefined;
  ChatScreen: undefined;
  RegisterScreen: undefined;
  AdminHomeScreen: undefined;
  AdminPedidosScreen: undefined;
  AdminCardapioScreen: undefined;
  AdminClientesScreen: undefined;
  
};

export type RootStackNavigationProp = NativeStackNavigationProp<RootStackParamList>;
export type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'LoginScreen'>;
export type ChatScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'ChatScreen'>;
export type RegisterScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterScreen'>;
export type AdminHomeScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminHomeScreen'>;
export type AdminPedidosScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminPedidosScreen'>;
export type AdminCardapioScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminCardapioScreen'>;
export type AdminClientesScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminClientesScreen'>;

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
        <Stack.Screen name="RegisterScreen" component={RegisterScreen} options={{ title: 'Área de Cadastro' }} />
        <Stack.Screen name="ChatScreen" component={ChatScreen} options={{ title: 'Popoli Chat Poliedro' }} />
        <Stack.Screen name="AdminHomeScreen" component={AdminHomeScreen} options={{ title: 'Painel de Administrador' }} />
        <Stack.Screen name="AdminPedidosScreen" component={AdminPedidosScreen} options={{ title: 'Gerenciar Pedidos' }} />
        <Stack.Screen name="AdminCardapioScreen" component={AdminCardapioScreen} options={{ title: 'Gerenciar Cardápio' }} />
        <Stack.Screen name="AdminClientesScreen" component={AdminClientesScreen} options={{ title: 'Clientes Cadastrados' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;