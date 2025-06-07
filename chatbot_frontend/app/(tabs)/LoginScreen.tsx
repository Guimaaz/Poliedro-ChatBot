import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Image, SafeAreaView, useWindowDimensions, Alert, ScrollView } from 'react-native';
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
  const [loginApiError, setLoginApiError] = useState('');

  const { width } = useWindowDimensions();
  const inputWidth = width < 600 ? width * 0.7 : 300;
  const containerWidth = width < 600 ? width * 0.9 : 500;
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const senhaInputRef = useRef<TextInput>(null);

  const handleLogin = async () => {
    setTelefoneError('');
    setSenhaError('');
    setLoginApiError('');

    let isValid = true;
    const limpatelefone = telefone.replace(/\D/g, '');

    if (!telefone) {
      setTelefoneError('Por favor, preencha o número de telefone.');
      isValid = false;
    } else if (limpatelefone.length < 11) {
      setTelefoneError('Número de telefone inválido.');
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
        body: JSON.stringify({ numero_cliente: telefone, senha }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        await AsyncStorage.setItem('userPhoneNumber', telefone);
        Alert.alert('Sucesso', 'Login realizado com sucesso!');
        if (data.is_admin === 1) {
          navigation.navigate('AdminHomeScreen');
        } else {
          navigation.navigate('ChatScreen');
        }
      } else {
        setLoginApiError(data.message || 'Falha ao realizar o login. Verifique suas credenciais.');
      }
    } catch (error) {
      console.error('Erro ao realizar login:', error);
      setLoginApiError('Ocorreu um erro ao comunicar com o servidor.');
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
    };
    checkPhoneNumber();
  }, []);

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
          <View style={styles.loginContainer}>
            <Text style={styles.title}>Login</Text>

            <View style={[styles.inputGroup, { width: inputWidth }]}>
              <TextInput
                style={styles.input}
                placeholder="Número de telefone"
                keyboardType="numbers-and-punctuation"
                value={telefone}
                onChangeText={text => {
                  setTelefone(formatPhoneNumber(text));
                  if (telefoneError) setTelefoneError('');
                  if (loginApiError) setLoginApiError('');
                }}
                maxLength={15}
                returnKeyType="next"
                onSubmitEditing={() => senhaInputRef.current?.focus()}
                placeholderTextColor="#000"
              />
              {telefoneError ? <Text style={styles.errorText}>{telefoneError}</Text> : null}
            </View>

            <View style={[styles.inputGroup, { width: inputWidth }]}>
              <TextInput
                ref={senhaInputRef}
                style={styles.input}
                placeholder="Senha"
                secureTextEntry
                value={senha}
                onChangeText={text => {
                  setSenha(text);
                  if (senhaError) setSenhaError('');
                  if (loginApiError) setLoginApiError('');
                }}
                returnKeyType="done"
                onSubmitEditing={handleLogin}
                placeholderTextColor="#000"
              />
              {senhaError ? <Text style={styles.errorText}>{senhaError}</Text> : null}
            </View>

            {loginApiError ? <Text style={[styles.errorText, styles.apiError]}>{loginApiError}</Text> : null}

            <TouchableOpacity
              style={[styles.button, { width: inputWidth > 250 ? inputWidth * 0.75 : inputWidth }]}
              onPress={handleLogin}
              disabled={loadingLogin}
            >
              <Text style={styles.buttonText}>{loadingLogin ? 'Entrando...' : 'Entrar'}</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={navigateToRegister} style={styles.registerLinkContainer}>
              <Text style={styles.registerLinkText}>Não tem uma conta? Cadastre-se</Text>
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
    height : '80%'
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
  registerLinkContainer: {
    marginTop: 25,
  },
  registerLinkText: {
    color: '#5C75A7',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});