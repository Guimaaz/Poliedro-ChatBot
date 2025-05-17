// AdminOrderList.tsx
import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { API_BASE_URL } from '../../utils/api';

interface Pedido {
  id: number;
  numero_cliente: string;
  item: string;
  preco: number;
  finalizado: boolean;
}

interface AdminOrderListProps {
  pedidosNaoFinalizados: Pedido[];
  onPedidoFinalizado: () => void;
}

const AdminOrderList: React.FC<AdminOrderListProps> = ({ pedidosNaoFinalizados, onPedidoFinalizado }) => {
  const [finalizandoPedidoId, setFinalizandoPedidoId] = useState<number | null>(null);

  const handleFinalizarPedido = async (pedidoId: number) => {
    setFinalizandoPedidoId(pedidoId);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/pedidos/${pedidoId}/finalizar`, {
        method: 'POST',
      });

      if (response.ok) {
        Alert.alert('Sucesso', `Pedido ${pedidoId} finalizado com sucesso!`);
        onPedidoFinalizado();
      } else {
        const errorData = await response.json();
        Alert.alert('Erro', errorData.message || `Falha ao finalizar o pedido ${pedidoId}.`);
      }
    } catch (error) {
      console.error('Erro ao finalizar pedido:', error);
      Alert.alert('Erro', 'Ocorreu um erro ao comunicar com o servidor.');
    } finally {
      setFinalizandoPedidoId(null);
    }
  };

  const renderItem = ({ item }: { item: Pedido }) => (
    <View style={styles.pedidoItem}>
      <Text>ID: {item.id}</Text>
      <Text>Cliente: {item.numero_cliente}</Text>
      <Text>Item: {item.item}</Text>
      <Text>Preço: R${item.preco.toFixed(2)}</Text>
      <TouchableOpacity
        style={[styles.finalizarButton, finalizandoPedidoId === item.id && styles.finalizandoButton]}
        onPress={() => handleFinalizarPedido(item.id)}
        disabled={finalizandoPedidoId === item.id || item.finalizado}
      >
        <Text style={styles.buttonText}>
          {finalizandoPedidoId === item.id ? 'Finalizando...' : 'Finalizar'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <FlatList
      data={pedidosNaoFinalizados}
      keyExtractor={(item) => String(item.id)}
      renderItem={renderItem}
    />
  );
};

const styles = StyleSheet.create({
  pedidoItem: {
    padding: 15,
    marginBottom: 10,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  finalizarButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 5,
    marginTop: 10,
    alignSelf: 'flex-start',
  },
  finalizandoButton: {
    backgroundColor: '#a9a9a9',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
  },
});

export default AdminOrderList;