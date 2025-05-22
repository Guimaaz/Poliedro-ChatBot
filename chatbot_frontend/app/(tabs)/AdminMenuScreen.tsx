import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ScrollView } from 'react-native';
import { API_BASE_URL } from '../../utils/api';
import AdminOrderList from './AdminOrderList';
import AdminMenuList from './AdminMenuList';

interface PedidoAgrupado {
  cliente: string;
  itens: string;
  preco_total: number;
  data_inicio: string;
  data_fim: string;
  finalizado: boolean;
}

interface MenuItem {
  id: number;
  pedido: string;
  preco: number;
}

const AdminHomeScreen = () => {
  const [pedidosNaoFinalizados, setPedidosNaoFinalizados] = useState<PedidoAgrupado[]>([]);
  const [pedidosFinalizados, setPedidosFinalizados] = useState<PedidoAgrupado[]>([]);
  const [loadingPedidos, setLoadingPedidos] = useState(true);
  const [menuItens, setMenuItens] = useState<MenuItem[]>([]);
  const [loadingMenu, setLoadingMenu] = useState(true);
  const [exibirPedidos, setExibirPedidos] = useState(true);

  const carregarPedidos = useCallback(async () => {
    setLoadingPedidos(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/pedidos`);
      if (response.ok) {
        const data = await response.json();
        setPedidosNaoFinalizados(data.nao_finalizados);
        setPedidosFinalizados(data.finalizados);
      } else {
        console.error('Falha ao carregar pedidos:', response);
    
      }
    } catch (error) {
      console.error('Erro ao carregar pedidos:', error);
     
    } finally {
      setLoadingPedidos(false);
    }
  }, []);

  const carregarCardapio = useCallback(async () => {
    setLoadingMenu(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/cardapio`);
      if (response.ok) {
        const data = await response.json();
        setMenuItens(data);
      } else {
        console.error('Falha ao carregar cardápio:', response);
      
      }
    } catch (error) {
      console.error('Erro ao carregar cardápio:', error);
      
    } finally {
      setLoadingMenu(false);
    }
  }, []);

  useEffect(() => {
    carregarPedidos();
    carregarCardapio();
  }, [carregarPedidos, carregarCardapio]);

  const handlePedidoFinalizado = useCallback(() => {
    carregarPedidos(); 
  }, [carregarPedidos]);

  const handleMenuItemUpdated = useCallback(() => {
    carregarCardapio(); 
  }, [carregarCardapio]);

  return (
    <ScrollView style={styles.scrollViewContainer}> 
      <View style={styles.container}>
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.tabButton, exibirPedidos && styles.activeTab]}
            onPress={() => setExibirPedidos(true)}
          >
            <Text style={[styles.tabButtonText, exibirPedidos && styles.activeTabText]}>Pedidos</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabButton, !exibirPedidos && styles.activeTab]}
            onPress={() => setExibirPedidos(false)}
          >
            <Text style={[styles.tabButtonText, !exibirPedidos && styles.activeTabText]}>Cardápio</Text>
          </TouchableOpacity>
        </View>

        {exibirPedidos ? (
          <View style={{ flex: 1 }}>
            <Text style={styles.title}>Pedidos Pendentes</Text>
            {loadingPedidos ? (
              <Text>Carregando pedidos...</Text>
            ) : (
              <View style={{ minHeight: 300 }}> {/* Removi o ScrollView daqui */}
                <AdminOrderList
                  pedidosNaoFinalizados={pedidosNaoFinalizados}
                  onPedidoFinalizado={handlePedidoFinalizado}
                />
              </View>
            )}

            {pedidosFinalizados.length > 0 && (
              <>
                <Text style={[styles.title, { marginTop: 10 }]}>Pedidos Finalizados</Text>
                <FlatList
                  data={pedidosFinalizados}
                  keyExtractor={(item) => item.cliente}
                  renderItem={({ item }) => (
                    <View style={styles.pedidoItem}>
                      <Text>Cliente: {item.cliente}</Text>
                      <Text>Itens:</Text>
                      <Text>{item.itens}</Text>
                      <Text>Preço Total: R${item.preco_total.toFixed(2)}</Text>
                      <Text>Data do Pedido: {item.data_inicio}</Text>
                      <Text style={{ color: 'green' }}>Finalizado</Text>
                    </View>
                  )}
                />
              </>
            )}
          </View>
        ) : (
          <View style={{ flex: 1 }}>
            <Text style={styles.title}>Cardápio</Text>
            {loadingMenu ? (
              <Text>Carregando cardápio...</Text>
            ) : (
              <AdminMenuList menuItens={menuItens} onMenuItemUpdated={handleMenuItemUpdated} />
            )}
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  scrollViewContainer: {
    flex: 1, 
  },
  container: {
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  pedidoItem: {
    padding: 15,
    marginBottom: 10,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  buttonContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#ddd',
    borderRadius: 5,
    marginHorizontal: 5,
  },
  activeTab: {
    backgroundColor: '#5C75A7',
  },
  tabButtonText: {
    fontSize: 16,
    color: '#333',
  },
  activeTabText: {
    color: '#fff',
  },
});

export default AdminHomeScreen;