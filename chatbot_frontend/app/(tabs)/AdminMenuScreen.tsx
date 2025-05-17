import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';

type AdminHomeScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminHomeScreen'>;

export default function AdminHomeScreen() {
  const navigation = useNavigation<AdminHomeScreenNavigationProp>();

  const navigateToPedidos = () => {
    navigation.navigate('AdminPedidosScreen');
  };

  const navigateToCardapio = () => {
    navigation.navigate('AdminCardapioScreen');
  };

  const navigateToClientes = () => {
    navigation.navigate('AdminClientesScreen');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Painel de Administrador</Text>

        <TouchableOpacity style={styles.button} onPress={navigateToPedidos}>
          <Text style={styles.buttonText}>Pedidos</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.button} onPress={navigateToCardapio}>
          <Text style={styles.buttonText}>Cardápio</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.button} onPress={navigateToClientes}>
          <Text style={styles.buttonText}>Clientes</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#4B3D3D',
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#e0e0e0',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 30,
    color: '#000',
    fontFamily: "Cal Sans"
  },
  button: {
    backgroundColor: '#5C75A7',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 25,
    marginBottom: 20,
    alignItems: 'center',
    width: 200,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
  },
});