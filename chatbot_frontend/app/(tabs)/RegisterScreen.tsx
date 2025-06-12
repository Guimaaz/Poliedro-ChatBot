import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Image, SafeAreaView, useWindowDimensions, Alert, ScrollView
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { API_BASE_URL } from '../../utils/api';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';

type RegisterScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'RegisterScreen'>;

const formatPhoneNumber = (text: string) => {
  const cleaned = text.replace(/\D/g, '');
  const maxLength = 11;
  const truncated = cleaned.substring(0, maxLength);
  let formatted = '';
  if (truncated.length === 0) return '';
  if (truncated.length <= 2) {
    formatted = `(${truncated}`;
  } else if (truncated.length <= 7) {
    formatted = `(${truncated.substring(0, 2)}) ${truncated.substring(2)}`;
  } else {
    formatted = `(${truncated.substring(0, 2)}) ${truncated.substring(2, 7)}-${truncated.substring(7)}`;
  }
  return formatted;
};

export default function RegisterScreen() {
  const [telefone, setTelefone] = useState('');
  const [senha, setSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [loadingRegister, setLoadingRegister] = useState(false);

  const [telefoneError, setTelefoneError] = useState('');
  const [senhaError, setSenhaError] = useState('');
  const [confirmarSenhaError, setConfirmarSenhaError] = useState('');
  const [registerApiError, setRegisterApiError] = useState('');

  const { width } = useWindowDimensions();
  const inputWidth = width < 600 ? width * 0.7 : 300;
  const containerWidth = width < 600 ? width * 0.9 : 500;

  const navigation = useNavigation<RegisterScreenNavigationProp>();

  const handleRegister = async () => {
    let isValid = true;
    const cleanedPhone = telefone;

    setTelefoneError('');
    setSenhaError('');
    setConfirmarSenhaError('');
    setRegisterApiError('');

    if (!telefone) {
      setTelefoneError('Por favor, preencha o número de telefone.');
      isValid = false;
    } 
   
    else if (cleanedPhone.length < 11) { 
      setTelefoneError('Número de telefone deve ter 11 dígitos.');
      isValid = false;
    }

    if (!senha) {
      setSenhaError('Por favor, preencha a senha.');
      isValid = false;
    }

    if (!confirmarSenha) {
      setConfirmarSenhaError('Por favor, confirme a senha.');
      isValid = false;
    } else if (senha && confirmarSenha && senha !== confirmarSenha) {
      setConfirmarSenhaError('As senhas não coincidem.');
      isValid = false;
    }

    if (!isValid) {
      return;
    }

    setLoadingRegister(true);
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ numero_cliente: cleanedPhone, senha }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        Alert.alert('Sucesso', data.message || 'Cadastro realizado com sucesso!');
        navigation.navigate('LoginScreen');
      } else {
        setRegisterApiError(data.message || 'Falha ao realizar o cadastro. Tente novamente.');
      }
    } catch (error) {
      console.error('Erro ao comunicar com o servidor:', error);
      setRegisterApiError('Ocorreu um erro ao comunicar com o servidor.');
    } finally {
      setLoadingRegister(false);
    }
  };

  const navigateToLogin = () => {
    navigation.navigate('LoginScreen');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.mainScrollView}
        contentContainerStyle={styles.mainScrollViewContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
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

            <View style={[styles.inputGroup, { width: inputWidth }]}>
              <TextInput
                style={styles.input}
                placeholder="Número de telefone"
                keyboardType="numbers-and-punctuation"
                value={telefone}
                onChangeText={text => {
                  setTelefone(formatPhoneNumber(text));
                  if (telefoneError) setTelefoneError('');
                  if (registerApiError) setRegisterApiError('');
                }}
                maxLength={15}
                placeholderTextColor="#000"
              />
              {telefoneError ? <Text style={styles.errorText}>{telefoneError}</Text> : null}
            </View>

            <View style={[styles.inputGroup, { width: inputWidth }]}>
              <TextInput
                style={styles.input}
                placeholder="Senha"
                secureTextEntry
                value={senha}
                onChangeText={text => {
                  setSenha(text);
                  if (senhaError) setSenhaError('');
                  if (registerApiError) setRegisterApiError('');
                }}
                placeholderTextColor="#000"
              />
              {senhaError ? <Text style={styles.errorText}>{senhaError}</Text> : null}
            </View>

            <View style={[styles.inputGroup, { width: inputWidth }]}>
              <TextInput
                style={styles.input}
                placeholder="Confirmar Senha"
                secureTextEntry
                value={confirmarSenha}
                onChangeText={text => {
                  setConfirmarSenha(text);
                  if (confirmarSenhaError) setConfirmarSenhaError('');
                  if (registerApiError) setRegisterApiError('');
                }}
                placeholderTextColor="#000"
              />
              {confirmarSenhaError ? <Text style={styles.errorText}>{confirmarSenhaError}</Text> : null}
            </View>

            {registerApiError ? <Text style={[styles.errorText, styles.apiError]}>{registerApiError}</Text> : null}

            <TouchableOpacity
              style={styles.button}
              onPress={handleRegister}
              disabled={loadingRegister}
            >
              <Text style={styles.buttonText}>{loadingRegister ? 'Cadastrando...' : 'Cadastrar'}</Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={navigateToLogin} style={styles.loginLinkContainer}>
              <Text style={styles.loginLinkText}>Já tem uma conta? Faça login</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.bottomRounded} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#4B3D3D',
  },
  mainScrollView: {
    flex: 1,
  },
  mainScrollViewContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  container: {
    backgroundColor: '#e0e0e0',
    borderRadius: 30,
    marginVertical: 20,
    marginHorizontal: 20,
    overflow: 'hidden',
    alignSelf: 'center',
    height : '90%'

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
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 30,
    paddingBottom: 30,
    height : '80%'
  },
  title: {
    fontSize: 28,
    marginBottom: 30,
    color: '#000',
    textAlign: 'center',
  },
  inputGroup: {
    minHeight: 74,
    marginBottom: 20,
    alignItems: 'flex-start',
    justifyContent: 'flex-start',
  },
  input: {
    height: 50,
    backgroundColor: '#fff',
    borderRadius: 25,
    paddingHorizontal: 20,
    fontSize: 16,
    color: '#000',
    width: '100%',
  },
  errorText: {
    color: 'red',
    fontSize: 12,
    marginTop: 6,
    paddingLeft: 20,
  },
  apiError: {
    textAlign: 'center',
    width: '100%',
    marginBottom: 15,
    marginTop: -10,
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
    height: 100,
    backgroundColor: '#5497f0',
  },
  loginLinkContainer: {
    marginTop: 25,
  },
  loginLinkText: {
    color: '#5C75A7',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});