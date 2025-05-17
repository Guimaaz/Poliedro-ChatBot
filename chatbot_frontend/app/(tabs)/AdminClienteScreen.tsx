import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, SafeAreaView, FlatList, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';
import { API_BASE_URL } from '../../utils/api';

interface Cliente {
  id: number;
  numero_cliente: string;
}

type AdminClientesScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminClientesScreen'>

// app/(tabs)/AdminClientesScreen.tsx (continuação)

export default function AdminClientesScreen() {
  const navigation = useNavigation<AdminClientesScreenNavigationProp>();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClientes();
  }, []);

  const fetchClientes = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/clientes`);
      if (!response.ok) {
        throw new Error(`Erro ao buscar clientes: ${response.status}`);
      }
      const data = await response.json();
      setClientes(data);
    } catch (error: any) {
      Alert.alert('Erro', error.message);
    } finally {
      setLoading(false);
    }
  };

  const renderClienteItem = ({ item }: { item: Cliente }) => (
    <View style={styles.clienteItem}>
      <Text>ID: {item.id}</Text>
      <Text>Número: {item.numero_cliente}</Text>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.container}>
          <Text>Carregando clientes...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Clientes Cadastrados</Text>
        <FlatList
          data={clientes}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderClienteItem}
          ListEmptyComponent={<Text>Nenhum cliente cadastrado.</Text>}
        />
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
    padding: 16,
    backgroundColor: '#e0e0e0',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#000',
    fontFamily: "Cal Sans"
  },
  clienteItem: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderColor: '#ccc',
    borderWidth: 1,
  },
});