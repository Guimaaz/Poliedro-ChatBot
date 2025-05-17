import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, SafeAreaView, FlatList, TouchableOpacity, TextInput, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';
import { API_BASE_URL } from '../../utils/api';

interface ItemCardapio {
  id: number;
  pedido: string;
  preco: number;
}

type AdminCardapioScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AdminCardapioScreen'>;

export default function AdminCardapioScreen() {
  const navigation = useNavigation<AdminCardapioScreenNavigationProp>();
  const [cardapio, setCardapio] = useState<ItemCardapio[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editText, setEditText] = useState('');
  const [editPreco, setEditPreco] = useState('');

  useEffect(() => {
    fetchCardapio();
  }, []);

  const fetchCardapio = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/admin/cardapio`);
      if (!response.ok) {
        throw new Error(`Erro ao buscar cardápio: ${response.status}`);
      }
      const data = await response.json();
      setCardapio(data);
    } catch (error: any) {
      Alert.alert('Erro', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (item: ItemCardapio) => {
    setEditingItemId(item.id);
    setEditText(item.pedido);
    setEditPreco(item.preco.toString());
  };

  const handleSave = async (itemId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/cardapio/${itemId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pedido: editText, preco: parseFloat(editPreco) }),
      });
      if (!response.ok) {
        throw new Error(`Erro ao salvar item: ${response.status}`);
      }
      Alert.alert('Sucesso', 'Item atualizado com sucesso!', [], { onDismiss: fetchCardapio });
      setEditingItemId(null);
    } catch (error: any) {
      Alert.alert('Erro', error.message);
    }
  };

  const handleDelete = async (itemId: number) => {
    Alert.alert(
      'Confirmar Exclusão',
      'Tem certeza que deseja excluir este item?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Excluir',
          style: 'destructive',
          onPress: async () => {
            try {
              const response = await fetch(`${API_BASE_URL}/admin/cardapio/${itemId}`, {
                method: 'DELETE',
              });
              if (!response.ok) {
                throw new Error(`Erro ao excluir item: ${response.status}`);
              }
              Alert.alert('Sucesso', 'Item excluído com sucesso!', [], { onDismiss: fetchCardapio });
            } catch (error: any) {
              Alert.alert('Erro', error.message);
            }
          },
        },
      ],
      { cancelable: false }
    );
  };

  const renderItem = ({ item }: { item: ItemCardapio }) => (
    <View style={styles.item}>
      {editingItemId === item.id ? (
        <>
          <TextInput style={styles.input} value={editText} onChangeText={setEditText} />
          <TextInput style={styles.input} value={editPreco} onChangeText={setEditPreco} keyboardType="numeric" />
          <TouchableOpacity style={styles.saveButton} onPress={() => handleSave(item.id)}>
            <Text style={styles.buttonText}>Salvar</Text>
          </TouchableOpacity>
        </>
      ) : (
        <>
          <Text style={styles.itemName}>{item.pedido}</Text>
          <Text style={styles.itemPrice}>R${item.preco.toFixed(2)}</Text>
          <View style={styles.buttonContainer}>
            <TouchableOpacity style={styles.editButton} onPress={() => handleEdit(item)}>
              <Text style={styles.buttonText}>Editar</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.deleteButton} onPress={() => handleDelete(item.id)}>
              <Text style={styles.buttonText}>Excluir</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.container}>
          <Text>Carregando cardápio...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Gerenciar Cardápio</Text>
        <FlatList
          data={cardapio}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
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
  item: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderColor: '#ccc',
    borderWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  itemName: {
    fontSize: 16,
    flex: 2,
  },
  itemPrice: {
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  buttonContainer: {
    flexDirection: 'row',
    marginLeft: 10,
  },
  editButton: {
    backgroundColor: 'orange',
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 5,
    marginLeft: 5,
  },
  deleteButton: {
    backgroundColor: 'red',
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 5,
    marginLeft: 5,
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
  },
  input: {
    flex: 1,
    height: 40,
    borderColor: 'gray',
    borderWidth: 1,
    borderRadius: 5,
    paddingHorizontal: 10,
    marginBottom: 5,
  },
  saveButton: {
    backgroundColor: 'green',
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 5,
    marginLeft: 5,
  },
});