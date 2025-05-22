//testada
import React, { useState, useEffect, useRef } from 'react'; 
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
  const [loadingLogin, setLoadingLogin] = useState(false);
  const { width } = useWindowDimensions();
  const inputWidth = width < 600 ? width * 0.7 : 300;
  const containerWidth = width < 600 ? width * 0.9 : 500;
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const senhaInputRef = useRef<TextInput>(null); 

  const handleLogin = async () => {
    if (!telefone || !senha) {
      Alert.alert('Erro', 'Por favor, preencha todos os campos.');
      return;
    }

    setLoadingLogin(true);
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
      console.log('Tipo de data.is_admin:', typeof data.is_admin); 

      if (response.ok && data.success) {
        await AsyncStorage.setItem('userPhoneNumber', telefone);
        Alert.alert('Sucesso', 'Login realizado com sucesso!');

        console.log('Valor de data.is_admin antes da navegação:', data.is_admin);

        if (data.is_admin === 1) {
          console.log('Navegando para AdminHomeScreen');
          navigation.navigate('AdminHomeScreen');
        } else {
          console.log('Navegando para ChatScreen');
          navigation.navigate('ChatScreen');
        }
      } else {
        Alert.alert('Erro', data.message || 'Falha ao realizar o login. Verifique suas credenciais.');
      }
    } catch (error) {
      console.error('Erro ao realizar login:', error);
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

          <TextInput
            style={[styles.input, { width: inputWidth }]}
            placeholder="Número de telefone"
            keyboardType="numbers-and-punctuation"
            value={telefone}
            onChangeText={setTelefone}
            returnKeyType="next"
            onSubmitEditing={() => senhaInputRef.current?.focus()} 
          />

          <TextInput
            ref={senhaInputRef}
            style={[styles.input, { width: inputWidth }]}
            placeholder="Senha"
            secureTextEntry
            value={senha}
            onChangeText={setSenha}
            returnKeyType="done"
            onSubmitEditing={handleLogin} 
          />

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
  registerLinkContainer: {
    marginTop: 20,
  },
  registerLinkText: {
    color: '#5C75A7',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});