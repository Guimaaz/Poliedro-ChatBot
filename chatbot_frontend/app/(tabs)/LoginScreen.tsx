import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Image, SafeAreaView, useWindowDimensions, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';
import { API_BASE_URL } from '../../utils/api';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';

type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'LoginScreen'>;

export default function LoginScreen() {
  const [telefone, setTelefone] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const { width } = useWindowDimensions();
  const inputWidth = width < 600 ? width * 0.7 : 700;
  const containerWidth = width < 600 ? width * 0.9 : 1000;
  const navigation = useNavigation<LoginScreenNavigationProp>();

  const handleLogin = async () => {
    if (!telefone || !senha) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos.');
      return;
    }

    setLoading(true);
    console.log('Fazendo requisição de login...', { numero_cliente: telefone, senha });
    try {
    const response = await fetch(`${API_BASE_URL}/login`, {
  method: 'POST', 
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ numero_cliente: telefone, senha }),
});

    console.log('Resposta bruta da API de login:', response); 
    const data = await response.json();
    console.log('Dados da resposta da API de login:', data); 

    if (response.ok && data.success) {
      await AsyncStorage.setItem('userPhoneNumber', telefone);
      Alert.alert('Sucesso', 'Login realizado com sucesso!');
      navigation.navigate('ChatScreen');
    } else {
      Alert.alert('Erro', data.message || 'Falha ao realizar o login. Verifique suas credenciais.');
    }
  } catch (error) {
    console.error('Erro ao realizar login:', error);
    Alert.alert('Erro', 'Ocorreu um erro ao comunicar com o servidor.');
  } finally {
    setLoading(false);
  }
};

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={[styles.container, { width: containerWidth }]}>
        <View style={styles.topContainer}>
          <Image
            source={require('../../assets/images/logopoliedro.png')}
            style={styles.logo}
            resizeMode="contain"
          />
        </View>

        <View style={styles.loginContainer}>
          <Text style={styles.title}>Login</Text>

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Número de telefone"
            keyboardType="phone-pad"
            value={telefone}
            onChangeText={setTelefone}
          />

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Senha"
            secureTextEntry
            value={senha}
            onChangeText={setSenha}
          />

          <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loading}>
            <Text style={styles.buttonText}>{loading ? 'Entrando...' : 'Entrar'}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.bottomRounded} />
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
    backgroundColor: '#e0e0e0',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    margin: 20,
    overflow: 'hidden',
    alignSelf: 'center'
  },
  topContainer: {
    backgroundColor: '#fff',
    paddingTop: 20,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderColor: '#ccc',
    paddingBottom: 10,
  },
  logo: {
    width: 120,
    height: 50,
  },
  loginContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    marginBottom: 40,
    color: '#000',
    
  },
  input: {
    height: 50,
    backgroundColor: '#fff',
    borderRadius: 25,
    paddingHorizontal: 20,
    fontSize: 16,
    marginBottom: 20,
  },
  button: {
    width: 150,
    backgroundColor: '#5497f0',
    paddingVertical: 12,
    borderRadius: 25,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
  },
  bottomRounded: {
    height: 50,
    backgroundColor: '#54977',
  },
});