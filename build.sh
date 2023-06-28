#! /bin/bash
set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes
set -x           # for debugging only: print last executed command




SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if docker compose version > /dev/null 2>&1
then
    COMPOSE="docker compose"
elif command -v docker-compose > /dev/null 2>&1
then
    COMPOSE="docker-compose"
else
    echo "Can't find docker-compose on this system."
    exit 1
fi
echo "Using compose command $COMPOSE"


function misses_image {
    # Function for boolean checks if an image already exists.
    # Uses the docker image inspect command. If it
    # finds the according image we can be save that it is there.
    # This is bettern then an docker image ls & a grep check.
    #
    # Arguments:
    #  - $1 => imageName - Name of the image that we want to check.
    #                      Supports normal image names, but also tags
    #                      or ids.
    imageName=$1
    if [[ -z $(docker image inspect --format '{{.Id}}' "$imageName" 2> /dev/null) ]]; then
        return
    else
        false
    fi
}

function clean {
    # Ensures that we can restart our script from an completely clean state.
    rm -rf config
    rm -rf styles
    rm -rf gfz-command-line-tool-repository
    rm -rf quakeledger
    rm -rf shakyground-grid-file
    rm -rf shakyground
    rm -rf assetmaster
    rm -rf modelprop
    rm -rf deus
    rm -rf tsunami-wps
    rm -rf dlr-riesgos-frontend
    rm -rf backend
    rm -rf compare-frontend
    rm -rf frontend
    rm -rf monitor
    docker image rm "gfzriesgos/riesgos-wps" || echo "Skip deleting image"
    docker image rm "gfzriesgos/quakeledger" || echo "Skip deleting image"
    docker image rm "gfzriesgos/shakyground-grid-file" || echo "Skip deleting image"
    docker image rm "gfzriesgos/shakyground" || echo "Skip deleting image"
    docker image rm "gfzriesgos/assetmaster" || echo "Skip deleting image"
    docker image rm "gfzriesgos/modelprop" || echo "Skip deleting image"
    docker image rm "gfzriesgos/deus" || echo "Skip deleting image"
    docker image rm "buildall-backend"  || echo "Skip deleting image"
    docker image rm "buildall-monitor"  || echo "Skip deleting image"
    docker image rm "buildall-frontend"  || echo "Skip deleting image"
    docker image rm "buildall-compare-frontend"  || echo "Skip deleting image"
    docker volume rm buildall_logs
    docker volume rm buildall_store
}

function build_riesgos_wps {
    image="gfzriesgos/riesgos-wps"
    repo="https://github.com/riesgos/gfz-command-line-tool-repository"
    if misses_image $image; then
            echo "Building $image ... "
            if [ ! -d gfz-command-line-tool-repository ]; then
                git clone "$repo"
            fi
            cd gfz-command-line-tool-repository
            docker build -t $image:latest -f assistance/Dockerfile .
            cd $SCRIPT_DIR
    else
            echo "Already exists: $image"
    fi
    if [ ! -d "styles" ]; then
        mkdir -p "styles"
    fi
    if [ ! -f "styles/shakemap-pga.sld" ]; then
        if [ ! -f "gfz-command-line-tool-repository/assistance/SLD/shakemap-pga.sld" ]; then
            git clone "$repo"
        fi
        cp gfz-command-line-tool-repository/assistance/SLD/* styles
    fi

}

function build_quakeledger {
    image="gfzriesgos/quakeledger"
    repo="https://github.com/gfzriesgos/quakeledger"
    if misses_image $image; then
            echo "Building $image ..."
            if [ ! -d quakeledger ]; then
                git clone "$repo"
            fi
            cd quakeledger
            docker image build --tag $image:latest --file ./metadata/Dockerfile .
            cd $SCRIPT_DIR
    else
            echo "Already exists: $image"
    fi
    # And add the json config to our configs folder.
    if [ ! -d "configs" ]; then
        mkdir -p "configs"
    fi
    if [ ! -f "config/quakeledger.json" ]; then
        if [ ! -f "quakeledger/metadata/quakeledger.json" ]; then
            git clone "$repo"
        fi
        cp quakeledger/metadata/quakeledger.json configs
    fi
}

function build_shakyground_grid {
    # We reuse this new image later as the base image for shakyground.
    # So that all the grid files are already there.
    image="gfzriesgos/skakyground-grid-file"
    repo="https://github.com/gfzriesgos/shakyground-grid-file"
    if misses_image $image; then
        if [ ! -d shakyground-grid-file ]; then
            git clone "$repo"
        fi
        cd shakyground-grid-file
        docker image build --tag $image:latest --file ./Dockerfile .
        cd $SCRIPT_DIR
    else
        echo "Already exists: $image"
    fi
}

function build_shakyground {
    image="gfzriesgos/shakyground"
    repo="https://github.com/gfzriesgos/shakyground"
    if misses_image $image; then
            echo "Building $image ..."
            if [ ! -d shakyground ]; then
                git clone "$repo"
            fi
            cd shakyground
            # Replace the FROM entry in the dockerfile
            # so that we use our latest shakyground-grid-file image
            sed -i -e 's/FROM gfzriesgos\/shakyground-grid-file:20211011/FROM gfzriesgos\/skakyground-grid-file:latest/' ./metadata/Dockerfile
            docker image build --tag $image:latest --file ./metadata/Dockerfile .
            cd $SCRIPT_DIR
    else
            echo "Already exists: $image"
    fi
    # And add the json config to our configs folder.
    if [ ! -d "configs" ]; then
        mkdir -p "configs"
    fi
    if [ ! -f "config/shakyground.json" ]; then
        if [ ! -f "shakyground/metadata/shakyground.json" ]; then
            git clone "$repo"
        fi
        cp shakyground/metadata/shakyground.json configs
    fi
}

function build_assetmaster {
    image="gfzriesgos/assetmaster"
    repo="https://github.com/gfzriesgos/assetmaster"
    if misses_image $image; then
        echo "Building $image ..."
        if [ ! -d assetmaster ]; then
            git clone "$repo"
        fi
        cd assetmaster
        docker image build --tag $image --file ./metadata/Dockerfile .
        cp metadata/assetmaster.json ../configs
        cd $SCRIPT_DIR
    else
        echo "Already exists: $image"
    fi
    # And add the json config to our configs folder.
    if [ ! -d "configs" ]; then
        mkdir -p "configs"
    fi
    if [ ! -f "config/assetmaster.json" ]; then
        if [ ! -f "assetmaster/metadata/assetmaster.json" ]; then
            git clone "$repo"
        fi
        cp assetmaster/metadata/assetmaster.json configs
    fi
}

function build_modelprop {
    image="gfzriesgos/modelprop"
    repo="https://github.com/gfzriesgos/modelprop"
    if misses_image $image; then
        echo "Building $image ..."
        if [ ! -d modelprop ]; then
            git clone "$repo"
        fi
        cd modelprop
        docker image build --tag $image --file ./metadata/Dockerfile .
        cd $SCRIPT_DIR
    else
        echo "Already exists: $image"
    fi
    # And add the json config to our configs folder.
    if [ ! -d "configs" ]; then
        mkdir -p "configs"
    fi
    if [ ! -f "config/modelprop.json" ]; then
        if [ ! -f "modelprop/metadata/modelprop.json" ]; then
            git clone "$repo"
        fi
        cp modelprop/metadata/modelprop.json configs
    fi
}

function build_deus {
    image="gfzriesgos/deus"
    repo="https://github.com/gfzriesgos/deus"
    if misses_image $image; then
        echo "Building $image ..."
        if [ ! -d deus ]; then
            git clone "$repo"
        fi
        cd deus
        docker image build --tag $image --file ./metadata/Dockerfile .
        cp metadata/deus.json ../configs
        cd $SCRIPT_DIR
    else
        echo "Already exists: $image"
    fi
    if [ ! -d "configs" ]; then
        mkdir -p "configs"
    fi
    if [ ! -f "config/deus.json" ]; then
        if [ ! -f "deus/metadata/deus.json" ]; then
            git clone "$repo"
        fi
        cp deus/metadata/deus.json configs
    fi
    # The json configuration files for neptunus & volcanus
    # belong to deus. So copy them as well.
    if [ ! -f "config/volcanus.json" ]; then
        if [ ! -f "deus/metadata/volcanus.json" ]; then
            git clone "$repo"
        fi
        cp deus/metadata/volcanus.json configs
    fi
    if [ ! -f "config/neptunus.json" ]; then
        if [ ! -f "deus/metadata/neptunus.json" ]; then
            git clone "$repo"
        fi
        cp deus/metadata/neptunus.json configs
    fi
}

function build_tssim {
    image="awi/tssim"
    if misses_image $image; then
            echo "Building $image ..."
            if [ ! -d "tsunami-wps" ]; then
                git clone https://gitlab.awi.de/tsunawi/web-services/tsunami-wps
            fi
            cd tsunami-wps
            git checkout full-docker-build-config
            curl https://nextcloud.awi.de/s/aNXgXxN9qk5RZRz/download/riesgos_tsunami_data.tgz -o riesgos_tsunami_data.tgz
            tar -xzf riesgos_tsunami_data.tgz
			rm riesgos_tsunami_data.tgz
            curl https://nextcloud.awi.de/s/rMGYacxWzM9y5PX/download/riesgos_tsunami_inun_data.tgz -o riesgos_tsunami_inun_data.tgz
            tar -xzf riesgos_tsunami_inun_data.tgz
            rm riesgos_tsunami_inun_data.tgz
            $COMPOSE build
            cd $SCRIPT_DIR
    else
            echo "Already exists: $image"
    fi
}

function build_sysrel {
    #TODO maybe split docker-compose to build one image each (currently -single and -multi are built together)
    image="52north/tum-era-critical-infrastructure-analysis-multi"
    if misses_image $image; then
            echo "Building $image ..."
            if [ ! -d "tum-era-critical-infrastructure-analysis" ]; then
                git clone https://github.com/52North/tum-era-critical-infrastructure-analysis
            fi
            cd tum-era-critical-infrastructure-analysis
            docker compose build
            cd javaPS
            docker compose build 
    else
            echo "Already exists: $image"
    fi
}

function build_frontend {

    # Making sure repo was cloned (needed even if images are already built)
    if [ ! -d "dlr-riesgos-frontend" ]; then

        # cleaning up potential artifacts of last build
        rm -rf backend
        rm -rf compare-frontend
        rm -rf frontend
        rm -rf monitor
        rm -rf docker-compose.dlr.yml

        # downloading and unpacking source code
        git clone https://github.com/riesgos/dlr-riesgos-frontend --branch=compare-frontend # --branch=2.0.6-main <-- once we have a stable tag
        mv dlr-riesgos-frontend/docker-compose.yml ./docker-compose.dlr.yml
        mv dlr-riesgos-frontend/backend ./
        mv dlr-riesgos-frontend/monitor ./
        mv dlr-riesgos-frontend/frontend ./
        mv dlr-riesgos-frontend/compare-frontend ./

        # clean up again
        rm -rf dlr-riesgos-frontend
    fi

    # Checking if rebuilding is required
    buildIt=false
    frontendImages=("buildall-frontend" "buildall-compare-frontend" "buildall-monitor" "buildall-backend")
    for image in "${frontendImages[@]}"
    do
        if misses_image "$image"; then
            buildIt=true
        fi
    done

    # Build if required
    if [ "$buildIt" = false ]; then
        echo "Already exists: frontend"
    else
        $COMPOSE -f docker-compose.dlr.yml build
        cd $SCRIPT_DIR
    fi
}

function build_all {
    build_riesgos_wps
    build_quakeledger
    build_shakyground_grid
    build_shakyground
    build_assetmaster
    build_modelprop
    build_deus
    # build_tssim
    build_sysrel
    build_frontend
}

function run_all {
    # @TODO: include here compose file by 52N
    echo "Effective config file:"
    $COMPOSE -f docker-compose.yml -f docker-compose.dlr.yml --env-file .env config
    echo "Running containers:"
    # At least initially: not starting monitor - causes a lot of load at once.
    $COMPOSE -f docker-compose.yml -f docker-compose.dlr.yml --env-file .env up -d wps-init riesgos-wps reverse_proxy backend frontend compare-frontend
}

function main {
    # Main function to dispatch to several actions.
    # Idea is to make the functions here easier to test.
    # If we give it an parameter, we invoke other functions.
    # If we don't give anohter parameter, then we run the
    # build_all.
    if [ -z ${1+x} ]; then
        # In case we don't have any subcommand then
        # we want to build and run all.
        build_all
    elif [ "$1" == "all" ]; then
        build_all
    elif [ "$1" == "run" ]; then
        run_all
    elif [ "$1" == "misses_image" ]; then
        image=$2
        if misses_image "$image"; then
            echo "$image is missing"
        else
            echo "$image is already there"
        fi
    elif [ "$1" == "clean" ]; then
        clean
    elif [ "$1" == "riesgos-wps" ]; then
        build_riesgos_wps
    elif [ "$1" == "quakeledger" ]; then
        build_quakeledger
    elif [ "$1" == "shakyground-grid" ]; then
        build_shakyground_grid
    elif [ "$1" == "shakyground" ]; then
        build_shakyground
    elif [ "$1" == "assetmaster" ]; then
        build_assetmaster
    elif [ "$1" == "modelprop" ]; then
        build_modelprop
    elif [ "$1" == "deus" ]; then
        build_deus
    elif [ "$1" == "tssim" ]; then
        build_tssim
    elif [ "$1" == "sysrel" ]; then
        build_sysrel
    elif [ "$1" == "frontend" ]; then
        build_frontend
    else
        echo "no known command found for: $1"
    fi
}

main "$@"




#echo "Building backend ..."
#echo "Building frontend ..."
#echo "Done!"
