//testada
import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Image, SafeAreaView, useWindowDimensions, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { API_BASE_URL } from '../../utils/api';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';

type RegisterScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterScreen'>;

export default function RegisterScreen() {
  const [telefone, setTelefone] = useState('');
  const [senha, setSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [loadingRegister, setLoadingRegister] = useState(false);
  const { width } = useWindowDimensions();
  const inputWidth = width < 600 ? width * 0.7 : 300;
  const containerWidth = width < 600 ? width * 0.9 : 500;
  const navigation = useNavigation<RegisterScreenNavigationProp>();

  const handleRegister = async () => {
    if (!telefone || !senha || !confirmarSenha) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos.');
      return;
    }

    if (senha !== confirmarSenha) {
      Alert.alert('Erro', 'As senhas não coincidem.');
      return;
    }

    setLoadingRegister(true);
    console.log('Fazendo requisição de cadastro...', { numero_cliente: telefone, senha });
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ numero_cliente: telefone, senha }),
      });

      console.log('Resposta bruta da API de cadastro:', response);
      const data = await response.json();
      console.log('Dados da resposta da API de cadastro:', data);

      if (response.ok && data.success) {
        Alert.alert('Sucesso', data.message || 'Cadastro realizado com sucesso!');
        navigation.navigate('LoginScreen');
      } else {
        Alert.alert('Erro', data.message || 'Falha ao realizar o cadastro.');
      }
    } catch (error) {
      console.error('Erro ao realizar cadastro:', error);
      Alert.alert('Erro', 'Ocorreu um erro ao comunicar com o servidor.');
    } finally {
      setLoadingRegister(false);
    }
  };

  const navigateToLogin = () => {
    navigation.navigate('LoginScreen');
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

        <View style={styles.registerContainer}>
          <Text style={styles.title}>Cadastro</Text>

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Número de telefone"
            keyboardType="numbers-and-punctuation"
            value={telefone}
            onChangeText={setTelefone}
            placeholderTextColor="#000"
          />

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Senha"
            secureTextEntry
            value={senha}
            onChangeText={setSenha}
            placeholderTextColor="#000"
          />

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Confirmar Senha"
            secureTextEntry
            value={confirmarSenha}
            onChangeText={setConfirmarSenha}
            placeholderTextColor="#000"
          />

          <TouchableOpacity style={styles.button} onPress={handleRegister} disabled={loadingRegister}>
            <Text style={styles.buttonText}>{loadingRegister ? 'Cadastrando...' : 'Cadastrar'}</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={navigateToLogin} style={styles.loginLinkContainer}>
            <Text style={styles.loginLinkText}>Já tem uma conta? Faça login</Text>
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
  registerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    marginBottom: 40,
    color: '#000',
    fontFamily: "Cal Sans"
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
    backgroundColor: '#5C75A7',
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
    backgroundColor: '#5C75A7',
  },
  loginLinkContainer: {
    marginTop: 20,
  },
  loginLinkText: {
    color: '#5C75A7',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});