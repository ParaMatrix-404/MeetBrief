pipeline {
    agent any

    stages {
        stage('Test and lint') {
            steps {
                sh '''
                    docker run --rm \
                        -v "$PWD:/workspace" \
                        -w /workspace \
                        python:3.14-slim \
                        sh -c "python -m pip install --no-cache-dir -r requirements-dev.txt && python -m pytest && python -m flake8 app.py tests"
                '''
            }
        }

        stage('Build MeetBrief image') {
            steps {
                sh 'docker build -t meetbrief:${BUILD_NUMBER} .'
            }
        }

        stage('Deploy to Render') {
            steps {
                withCredentials([string(
                    credentialsId: 'render-deploy-hook',
                    variable: 'RENDER_DEPLOY_HOOK'
                )]) {
                    sh '''
                        curl --fail --silent --show-error \
                            --request POST \
                            "$RENDER_DEPLOY_HOOK"
                    '''
                }
            }
        }
    }
}