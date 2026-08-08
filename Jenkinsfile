// Jenkinsfile
// Pipeline CI/CD del proyecto DataOps - Cálculo de comisiones de empleados.
//
// Requiere configurar en Jenkins (Manage Jenkins -> Credentials):
//   - Secret text con id "db-password"  -> valor: la contraseña de PostgreSQL
//
// El resto de variables de conexión (host, puerto, db, usuario) se dejan
// como variables de entorno en este mismo archivo porque no son secretas,
// solo la contraseña se maneja como credential.

pipeline {
    agent any

    environment {
        DB_HOST = 'mgg.vps.webdock.cloud'
        DB_PORT = '5432'
        DB_NAME = 'dmc'
        DB_USER = 'usr_ro_dmc_rrhh_estudiantes'
        DB_PASSWORD = credentials('db-password')
    }

    stages {
        stage('Checkout') {
            steps {
                    cleanWs()
                    checkout scm
            }
        }

        stage('CI - Instalar dependencias') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('CI - Tests unitarios') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python -m pytest tests/ -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('CD - Deploy & Run (Dev)') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python src/etl.py \
                        --csv data/ComisionEmpleados_V1_202608.csv \
                        --out output/dev/salario_total.parquet
                '''
            }
        }

        stage('Aprobación manual para Producción') {
            steps {
                input message: '¿Aprobar despliegue a Producción?', ok: 'Desplegar'
            }
        }

        stage('CD - Deploy & Run (Producción)') {
            steps {
                sh '''
                    . .venv/bin/activate
                    python src/etl.py \
                        --csv data/ComisionEmpleados_V1_202608.csv \
                        --out output/prod/salario_total.parquet
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completado con éxito: Dev y Producción desplegados.'
        }
        failure {
            echo 'El pipeline falló. Revisar logs de la etapa correspondiente.'
        }
        always {
            archiveArtifacts artifacts: 'output/**/*.parquet, output/**/*.xlsx', allowEmptyArchive: true
        }
    }
}
