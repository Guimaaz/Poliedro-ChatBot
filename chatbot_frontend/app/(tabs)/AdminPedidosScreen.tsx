// app/(tabs)/AdminPedidosScreen.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, SafeAreaView, FlatList, TouchableOpacity, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';
import { API_BASE_URL } from '../../utils/api';

interface Pedido {
  id: number;
  numero_cliente: string;
  item: string;
  preco: number;
  finalizado: boolean;
}

type AdminPedidosScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminPedidosScreen'>;

export default function AdminPedidosScreen() {
  const navigation = useNavigation<AdminPedidosScreenNavigationProp>();
  const [pedidosNaoFinalizados, setPedidosNaoFinalizados] = useState<Pedido[]>([]);
  const [pedidosFinalizados, setPedidosFinalizados] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPedidos();
  }, []);

  const fetchPedidos = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/pedidos`);
      if (!response.ok) {
        throw new Error(`Erro ao buscar pedidos: ${response.status}`);
      }
      const data = await response.json();
      setPedidosNaoFinalizados(data.nao_finalizados);
      setPedidosFinalizados(data.finalizados);
    } catch (error: any) {
      Alert.alert('Erro', error.message);
    } finally {
      setLoading(false);
    }
  };

  const finalizarPedido = async (pedidoId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/pedidos/${pedidoId}/finalizar`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Erro ao finalizar pedido: ${response.status}`);
      }
      Alert.alert('Sucesso', 'Pedido finalizado com sucesso!', [], { onDismiss: fetchPedidos });
    } catch (error: any) {
      Alert.alert('Erro', error.message);
    }
  };

  const reabrirPedido = async (pedidoId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/pedidos/${pedidoId}/reabrir`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Erro ao reabrir pedido: ${response.status}`);
      }
      Alert.alert('Sucesso', 'Pedido reaberto com sucesso!', [], { onDismiss: fetchPedidos });
    } catch (error: any) {
      Alert.alert('Erro', error.message);
    }
  };

  const renderPedidoItem = ({ item }: { item: Pedido }) => (
    <View style={styles.pedidoItem}>
      <Text>Cliente: {item.numero_cliente}</Text>
      <Text>ID do Pedido: {item.id}</Text>
      <Text>Item: {item.item}</Text>
      <Text>Preço: R${item.preco.toFixed(2)}</Text>
      {!item.finalizado ? (
        <TouchableOpacity style={styles.finalizarButton} onPress={() => finalizarPedido(item.id)}>
          <Text style={styles.buttonText}>Finalizar</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity style={styles.reabrirButton} onPress={() => reabrirPedido(item.id)}>
          <Text style={styles.buttonText}>Reabrir</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.container}>
          <Text>Carregando pedidos...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Pedidos Não Finalizados</Text>
        <FlatList
          data={pedidosNaoFinalizados}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderPedidoItem}
          ListEmptyComponent={<Text>Nenhum pedido pendente.</Text>}
        />

        <Text style={[styles.title, { marginTop: 20 }]}>Pedidos Finalizados</Text>
        <FlatList
          data={pedidosFinalizados}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderPedidoItem}
          ListEmptyComponent={<Text>Nenhum pedido finalizado.</Text>}
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
  pedidoItem: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderColor: '#ccc',
    borderWidth: 1,
  },
  finalizarButton: {
    backgroundColor: 'green',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 5,
    marginTop: 10,
    alignSelf: 'flex-start',
  },
  reabrirButton: {
    backgroundColor: 'orange',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 5,
    marginTop: 10,
    alignSelf: 'flex-start',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
  },
});