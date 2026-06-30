pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'your-dockerhub-username'
        IMAGE_NAME = 'your-app-name'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        COMPOSE_PROJECT_NAME = "app-${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                dir('backend') {
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --no-cache-dir -r requirements.txt
                    '''
                }
            }
        }

        stage('Lint') {
            steps {
                dir('backend') {
                    sh '''
                        . venv/bin/activate
                        pip install flake8
                        flake8 . --max-line-length=120 || true
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                dir('backend') {
                    sh '''
                        . venv/bin/activate
                        pip install pytest
                        pytest --junitxml=test-results.xml || true
                    '''
                }
            }
            post {
                always {
                    junit 'backend/test-results.xml'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}", "./backend")
                }
            }
        }

        stage('Integration Test (Docker Compose)') {
            steps {
                sh '''
                    docker compose -f docker-compose.yml up -d --build
                    sleep 15
                    curl -f http://localhost:5000/health || exit 1
                '''
            }
            post {
                always {
                    sh 'docker compose -f docker-compose.yml down -v'
                }
            }
        }

        stage('Push Docker Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'dockerhub-credentials') {
                        dockerImage.push("${IMAGE_TAG}")
                        dockerImage.push('latest')
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    docker compose -f docker-compose.yml pull
                    docker compose -f docker-compose.yml up -d
                '''
            }
        }
    }

    post {
        success {
            echo "Build #${env.BUILD_NUMBER} succeeded."
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} failed."
        }
        always {
            cleanWs()
        }
    }
}