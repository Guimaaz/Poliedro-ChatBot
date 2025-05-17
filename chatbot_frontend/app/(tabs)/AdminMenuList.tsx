// AdminMenuList.tsx
import React, { useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, TextInput } from 'react-native';
import { API_BASE_URL } from '../../utils/api';

interface MenuItem {
  id: number;
  pedido: string;
  preco: number;
}

interface AdminMenuListProps {
  menuItens: MenuItem[];
  onMenuItemUpdated: () => void;
}

const AdminMenuList: React.FC<AdminMenuListProps> = ({ menuItens, onMenuItemUpdated }) => {
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editedPedido, setEditedPedido] = useState('');
  const [editedPreco, setEditedPreco] = useState('');
  const [updatingItemId, setUpdatingItemId] = useState<number | null>(null);

  const handleEditarItem = (item: MenuItem) => {
    setEditingItemId(item.id);
    setEditedPedido(item.pedido);
    setEditedPreco(String(item.preco));
  };

  const handleSalvarEdicao = async (itemId: number) => {
    setUpdatingItemId(itemId);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/cardapio/${itemId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pedido: editedPedido, preco: parseFloat(editedPreco) }),
      });

      if (response.ok) {
        Alert.alert('Sucesso', `Item ${itemId} atualizado com sucesso!`);
        setEditingItemId(null);
        onMenuItemUpdated();
      } else {
        const errorData = await response.json();
        Alert.alert('Erro', errorData.message || `Falha ao atualizar o item ${itemId}.`);
      }
    } catch (error) {
      console.error('Erro ao atualizar item:', error);
      Alert.alert('Erro', 'Ocorreu um erro ao comunicar com o servidor.');
    } finally {
      setUpdatingItemId(null);
    }
  };

  const renderItem = ({ item }: { item: MenuItem }) => (
    <View style={styles.menuItem}>
      {editingItemId === item.id ? (
        <View>
          <TextInput
            style={styles.input}
            value={editedPedido}
            onChangeText={setEditedPedido}
            placeholder="Nome do Item"
          />
          <TextInput
            style={styles.input}
            value={editedPreco}
            onChangeText={setEditedPreco}
            placeholder="Preço"
            keyboardType="numeric"
          />
          <TouchableOpacity
            style={[styles.salvarButton, updatingItemId === item.id && styles.updatingButton]}
            onPress={() => handleSalvarEdicao(item.id)}
            disabled={updatingItemId === item.id}
          >
            <Text style={styles.buttonText}>
              {updatingItemId === item.id ? 'Salvando...' : 'Salvar'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.cancelarButton} onPress={() => setEditingItemId(null)}>
            <Text style={styles.buttonText}>Cancelar</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.itemInfo}>
          <Text>{item.pedido}</Text>
          <Text>R${item.preco.toFixed(2)}</Text>
          <TouchableOpacity style={styles.editarButton} onPress={() => handleEditarItem(item)}>
            <Text style={styles.buttonText}>Editar</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  return (
    <FlatList
      data={menuItens}
      keyExtractor={(item) => String(item.id)}
      renderItem={renderItem}
    />
  );
};

const styles = StyleSheet.create({
  menuItem: {
    padding: 15,
    marginBottom: 10,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  itemInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  editarButton: {
    backgroundColor: '#2196F3',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 5,
  },
  salvarButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 5,
    marginTop: 10,
  },
  cancelarButton: {
    backgroundColor: '#f44336',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 5,
    marginTop: 10,
  },
  updatingButton: {
    backgroundColor: '#a9a9a9',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
  },
  input: {
    height: 40,
    borderColor: 'gray',
    borderWidth: 1,
    marginBottom: 10,
    paddingHorizontal: 10,
    borderRadius: 5,
  },
});

export default AdminMenuList;