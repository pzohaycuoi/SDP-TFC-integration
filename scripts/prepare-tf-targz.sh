#!/bin/bash

git clone https://github.com/pzohaycuoi/learn-terraform-no-code-provisioning.git
cd learn-terraform-no-code-provisioning || exit
git archive --format=tar.gz  -o ../repo.tar.gz --prefix=learn-terraform-no-code-provisioning/ main
cd .. || exit
rm -rf learn-terraform-no-code-provisioning