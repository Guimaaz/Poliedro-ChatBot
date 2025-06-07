import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Image, SafeAreaView, useWindowDimensions, Alert
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';
import { API_BASE_URL } from '../../utils/api';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../navigation';

type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'LoginScreen'>;

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

export default function LoginScreen() {
  const [telefone, setTelefone] = useState('');
  const [senha, setSenha] = useState('');
  const [loadingLogin, setLoadingLogin] = useState(false);

  const [telefoneError, setTelefoneError] = useState('');
  const [senhaError, setSenhaError] = useState('');

  const { width } = useWindowDimensions();
  const inputWidth = width < 600 ? width * 0.7 : 300;
  const containerWidth = width < 600 ? width * 0.9 : 500;
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const senhaInputRef = useRef<TextInput>(null);

  const handleLogin = async () => {
    let isValid = true;
    const cleanedPhone = telefone.replace(/\D/g, '');

    setTelefoneError('');
    setSenhaError('');

    if (!telefone) {
      setTelefoneError('Por favor, preencha o número de telefone.');
      isValid = false;
    } else if (cleanedPhone.length < 11) {
        setTelefoneError('Número de telefone deve ter 11 dígitos.');
        isValid = false;
    }

    if (!senha) {
      setSenhaError('Por favor, preencha a senha.');
      isValid = false;
    }

    if (!isValid) {
      return;
    }

    setLoadingLogin(true);
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ numero_cliente: cleanedPhone, senha }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        await AsyncStorage.setItem('userPhoneNumber', cleanedPhone);
        Alert.alert('Sucesso', 'Login realizado com sucesso!');
        if (data.is_admin === 1) {
          navigation.navigate('AdminHomeScreen');
        } else {
          navigation.navigate('ChatScreen');
        }
      } else {
        Alert.alert('Erro', data.message || 'Falha ao realizar o login. Verifique suas credenciais.');
      }
    } catch (error) {
      console.error('Erro ao comunicar com o servidor:', error);
      Alert.alert('Erro', 'Ocorreu um erro ao comunicar com o servidor.');
    } finally {
      setLoadingLogin(false);
    }
  };

  const navigateToRegister = () => {
    navigation.navigate('RegisterScreen');
  };

  useEffect(() => {
    const checkPhoneNumber = async () => {
      const phoneNumber = await AsyncStorage.getItem('userPhoneNumber');
      console.log('Número de telefone no AsyncStorage:', phoneNumber);
    };
    checkPhoneNumber();
  }, []);

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

          <View style={[styles.inputWrapper, { width: inputWidth }]}>
            <TextInput
              style={styles.input}
              placeholder="Número de telefone"
              keyboardType="numbers-and-punctuation"
              value={telefone}
              onChangeText={text => {
                setTelefone(formatPhoneNumber(text));
                if (telefoneError) setTelefoneError('');
              }}
              maxLength={15}
              returnKeyType="next"
              onSubmitEditing={() => senhaInputRef.current?.focus()}
              placeholderTextColor="#000"
            />
            {telefoneError ? <Text style={styles.errorText}>{telefoneError}</Text> : null}
          </View>

          <View style={[styles.inputWrapper, { width: inputWidth }]}>
            <TextInput
              ref={senhaInputRef}
              style={styles.input}
              placeholder="Senha"
              secureTextEntry
              value={senha}
              onChangeText={text => {
                setSenha(text);
                if (senhaError) setSenhaError('');
              }}
              returnKeyType="done"
              onSubmitEditing={handleLogin}
              placeholderTextColor="#000"
            />
            {senhaError ? <Text style={styles.errorText}>{senhaError}</Text> : null}
          </View>

          <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={loadingLogin}>
            <Text style={styles.buttonText}>{loadingLogin ? 'Entrando...' : 'Entrar'}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={navigateToRegister} style={styles.registerLinkContainer}>
            <Text style={styles.registerLinkText}>Não tem uma conta? Cadastre-se</Text>
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
    borderRadius: 30,
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
  inputWrapper: {
    marginBottom: 20,
    width: '100%',
    alignItems: 'flex-start',
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
    backgroundColor: '#5497f0',
  },
  registerLinkContainer: {
    marginTop: 20,
  },
  registerLinkText: {
    color: '#5C75A7',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});