//testada
import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { API_BASE_URL } from '../../utils/api';

interface PedidoAgrupado {
  cliente: string;
  itens: string;
  preco_total: number;
  data_inicio: string;
  data_fim: string;
  finalizado: boolean;
}

interface AdminOrderListProps {
  pedidosNaoFinalizados: PedidoAgrupado[];
  onPedidoFinalizado: () => void;
}

const AdminOrderList: React.FC<AdminOrderListProps> = ({ pedidosNaoFinalizados, onPedidoFinalizado }) => {
  const [finalizandoCliente, setFinalizandoCliente] = useState<string | null>(null);

  const handleFinalizarPedidoAgrupado = async (cliente: string) => {
    setFinalizandoCliente(cliente);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/pedidos/cliente/${cliente}/finalizar`, {
        method: 'POST',
      });

      if (response.ok) {
        Alert.alert('Sucesso', `Pedidos de ${cliente} finalizados com sucesso!`);
        onPedidoFinalizado();
      } else {
        const errorData = await response.json();
        Alert.alert('Erro', errorData.message || `Falha ao finalizar os pedidos de ${cliente}.`);
      }
    } catch (error) {
      console.error('Erro ao finalizar pedidos:', error);
      Alert.alert('Erro', 'Ocorreu um erro ao comunicar com o servidor.');
    } finally {
      setFinalizandoCliente(null);
    }
  };

  const renderItem = ({ item }: { item: PedidoAgrupado }) => (
    <View style={styles.pedidoItem}>
      <Text>Cliente: {item.cliente}</Text>
      <Text>Itens:</Text>
      <Text>{item.itens}</Text>
      <Text>Preço Total: R${item.preco_total.toFixed(2)}</Text>
      <Text>Data do Pedido: {item.data_inicio}</Text>
      <TouchableOpacity
        style={[styles.finalizarButton, finalizandoCliente === item.cliente && styles.finalizandoButton]}
        onPress={() => handleFinalizarPedidoAgrupado(item.cliente)}
        disabled={finalizandoCliente === item.cliente || item.finalizado}
      >
        <Text style={styles.buttonText}>
          {finalizandoCliente === item.cliente ? 'Finalizando...' : 'Finalizar'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <FlatList
      data={pedidosNaoFinalizados}
      keyExtractor={(item) => item.cliente}
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